#!/usr/bin/python3
import os
import math

from opcode import *


class VersionError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class TypeConstructor(enum.IntEnum):
    def __repr__(self):
        return self.name
    i32 = 0x7f
    i64 = 0x7e
    f32 = 0x7d
    f64 = 0x7c
    anyfunc = 0x70
    func = 0x60
    empty_block = 0x40


class ExternalKind(enum.IntEnum):
    def __repr__(self):
        return f"Ext<{self.name}>"
    Function = 0
    Table = 1
    Memory = 2
    Global = 3


class NameType(enum.IntEnum):
    def __repr__(self):
        return f"N<{self.name}>"
    Module = 0
    Function = 1
    Local = 2


class ParseData:
    def __init__(self):
        self.custom_sections = []
        self.name_section = None
        self.type_section = None
        self.import_section = None
        self.function_section = None
        self.table_section = None
        self.memory_section = None
        self.global_section = None
        self.export_section = None
        self.start_section = None
        self.element_section = None
        self.code_section = None
        self.data_section = None


class Parser:
    magic_num = 0x6d736100
    supported_version = 0x1
    endOpcode = 0x0b

    resData = ParseData()

    def __init__(self, in_file):
        self.file = in_file
        self.file_offset = 0
        self.initOpcodeFn()

    def get_current_offset(self):
        return self.file_offset

    def get_read_len(self, old):
        return self.get_current_offset() - old

    def fileIsEof(self):
        file_len = os.fstat(self.file.fileno()).st_size
        return self.file.tell() == file_len

    def readBytes(self, l):
        self.file_offset += l
        return self.file.read(l)

    def readUTF8(self, l):
        return self.readBytes(l).decode("utf-8")

    def readUInt(self, l):
        return int.from_bytes(self.readBytes(l), byteorder='little')

    def readVarUintLen(self, l):
        res = 0
        shift = 0
        len = 0
        while True:
            len += 1
            byte = self.readUInt(1)
            res |= (0x7f & byte) << shift
            if (byte & 0x80) == 0:
                break
            shift += 7
        assert math.ceil(l / 7) <= l
        return res, len

    def readVarUint(self, l):
        return self.readVarUintLen(l)[0]

    def readVarIntLen(self, l):
        res = 0
        shift = 0
        size = 0
        len = 0
        while True:
            len += 1
            byte = self.readUInt(1)
            res |= (0x7f & byte) << shift
            shift += 7
            if (byte & 0x80) == 0:
                break
        if shift < size and (byte & 0x40) != 0:
            res |= (~0 << shift)
        assert math.ceil(l / 7) <= l
        return res, len

    def readVarInt(self, l):
        return self.readVarIntLen(l)[0]

    def read_type_constr(self):
        byte = self.readVarInt(7)
        type_c = TypeConstructor(byte)
        return type_c

    def read_fn_type(self):
        form = self.read_type_constr()
        param_count = self.readVarUint(32)
        param_types = []
        for i in range(param_count):
            param_type = self.parse_value_type()
            param_types.append(param_type)
        return_count = self.readVarUint(1)
        return_types = []
        for i in range(return_count):
            return_type = self.parse_value_type()
            return_types.append(return_type)
        return form, param_types, return_types

    def read_resizable_limits(self):
        limits_flag = self.readVarUint(1)
        limits_initial = self.readVarUint(32)
        if limits_flag == 1:
            limits_maximum = self.readVarUint(32)
        else:
            limits_maximum = None
        limits = (limits_flag, limits_initial, limits_maximum)
        return limits

    def read_init_expr(self):
        op = self.read_opcode()
        res = self.readUInt(1)
        if res != 0x0b:
            print("oops")
        assert res == 0x0b
        return op

    def read_memory_type(self):
        return self.read_resizable_limits()

    def read_table_type(self):
        elem_type = self.readVarUint(7)
        limits = self.read_resizable_limits()
        entry = (elem_type, limits)
        return entry

    def read_name_map(self):
        count = self.readVarUint(32)
        names = []
        for i in range(count):
            index = self.readVarUint(32)
            name_len = self.readVarUint(32)
            name_str = self.readUTF8(name_len)
            naming = (index, name_str)
            names.append(naming)
        return names

    # section parsing

    def parse_preamble(self):
        print("Parsing WASM header ...", end="")
        magic = self.readUInt(4)
        if magic != Parser.magic_num:
            print("%02x != %02x" % (magic, Parser.magic_num))
            raise Exception("not a wasm file!")
        version = self.readUInt(4)
        if version != Parser.supported_version:
            raise VersionError("only version 1 is supported currently")
        print(" OK")

    def parse_section(self):
        print(" ## Parsing section ...", end="")
        sec_id = self.readVarUint(7)
        payload_len = self.readVarUint(32)
        name_len_size = 0
        name_bytes = bytes()
        name = ""
        if sec_id == 0:
            name_len, name_len_size = self.readVarUintLen(32)
            name_bytes = self.readBytes(name_len)
            name = name_bytes.decode("utf-8")
            print("[name = '%s']" % name)
        else:
            print("[id = %d]" % sec_id)
        payload_data_len = payload_len - len(name_bytes) - name_len_size
        if sec_id == 0x0:
            if name == "name":
                self.resData.name_section = self.parse_name_custom_section(payload_data_len)
            else:
                self.resData.custom_sections.append(
                    self.parse_custom_section(name, payload_data_len))  # some other custom section
        elif sec_id == 0x1:
            self.resData.type_section = self.parse_type_section(payload_data_len)
        elif sec_id == 0x2:
            self.resData.import_section = self.parse_import_section(payload_data_len)
        elif sec_id == 0x3:
            self.resData.function_section = self.parse_function_section(payload_data_len)
        elif sec_id == 0x4:
            self.resData.table_section = self.parse_table_section(payload_data_len)
        elif sec_id == 0x5:
            self.resData.memory_section = self.parse_memory_section(payload_data_len)
        elif sec_id == 0x6:
            self.resData.global_section = self.parse_global_section(payload_data_len)
        elif sec_id == 0x7:
            self.resData.export_section = self.parse_export_section(payload_data_len)
        elif sec_id == 0x8:
            self.resData.start_section = self.parse_start_section(payload_data_len)
        elif sec_id == 0x9:
            self.resData.element_section = self.parse_element_section(payload_data_len)
        elif sec_id == 0xA:
            self.resData.code_section = self.parse_code_section(payload_data_len)
        elif sec_id == 0xB:
            self.resData.data_section = self.parse_data_section(payload_data_len)
        else:
            raise Exception("Unknown Section ID" + str(sec_id))
        print(" ++ Done parsing section")

    def parse_name_custom_section(self, payload_len):
        print("  # Parsing name custom section")
        init_offset = self.get_current_offset()
        name_module_section = None
        name_function_section = None
        name_local_section = None
        name_subsections = []
        while self.get_read_len(init_offset) < payload_len:
            name_type = NameType(self.readVarUint(7))
            name_payload_len = self.readVarUint(32)
            # enforce ordering and uniqueness of the sections with assertions
            if name_type == NameType.Module:
                assert name_module_section is None and name_function_section is None and name_local_section is None
                name_len = self.readVarUint(32)
                name_str = self.readUTF8(name_len)
                name_module_section = (name_str,)
            elif name_type == NameType.Function:
                assert name_function_section is None and name_local_section is None
                name_map = self.read_name_map()
                name_function_section = name_map
            elif name_type == NameType.Local:
                assert name_local_section is None
                count = self.readVarUint(32)
                funcs = []
                for i in range(count):
                    index = self.readVarUint(32)
                    local_map = self.read_name_map()
                    func = (index, local_map)
                    funcs.append(func)
                name_local_section = funcs
            else:
                name_payload_data = self.readBytes(name_payload_len)
                name_payload = name_payload_data
                subsection = (name_type, name_payload)
                name_subsections.append(subsection)
        assert self.get_read_len(init_offset) == payload_len
        result = (name_module_section, name_function_section, name_local_section, name_subsections)
        print(result)
        print("  + Parsing name custom section done")
        return result

    def parse_custom_section(self, name, payload_len):
        print("  # Parsing custom section")
        payload = self.readBytes(payload_len)
        print("Custom Section Data [len={:d}] = {}...".format(payload_len, payload[:32]))
        print("  + Parsing custom section done")
        return name, payload

    def parse_import_section(self, payload_len):
        print("  # Parsing import section")
        init_offset = self.get_current_offset()
        count = self.readVarUint(32)
        entries = []
        for i in range(count):
            module_len = self.readVarUint(32)
            module_str = self.readUTF8(module_len)
            field_len = self.readVarUint(32)
            field_str = self.readUTF8(field_len)
            kind = ExternalKind(self.readUInt(1))
            if kind == ExternalKind.Function:
                type = self.readVarUint(32)
            elif kind == ExternalKind.Table:
                type = self.read_table_type()
            elif kind == ExternalKind.Memory:
                type = self.read_memory_type()
            elif kind == ExternalKind.Global:
                type = self.read_global_type()
            else:
                assert False
            import_entry = (module_str, field_str, kind, type)
            entries.append(import_entry)
        assert self.get_read_len(init_offset) == payload_len
        print(entries)
        print("  + Parsing import section done")
        return entries

    def parse_type_section(self, payload_len):
        print("  # Parsing type section")
        init_offset = self.get_current_offset()
        count = self.readVarUint(32)
        types = []
        while self.get_read_len(init_offset) < payload_len:
            fnType = self.read_fn_type()
            types.append(fnType)
        assert self.get_read_len(init_offset) == payload_len
        print(types)
        print("  + Parsing type section done")
        return types

    def parse_value_type(self):
        ptype = self.readVarUint(7)
        param_type = TypeConstructor(ptype)
        return param_type

    def parse_function_section(self, payload_len):
        print("  # Parsing function section")
        init_offset = self.get_current_offset()
        count = self.readVarUint(32)
        types = []
        for i in range(count):
            type = self.readVarUint(32)
            types.append(type)
        assert self.get_read_len(init_offset) == payload_len
        print(types)
        print("  + Parsing function section done")
        return types

    def parse_table_section(self, payload_len):
        print("  # Parsing table section")
        init_offset = self.get_current_offset()
        count = self.readVarUint(32)
        entries = []
        for i in range(count):
            entry = self.read_table_type()
            entries.append(entry)
        assert self.get_read_len(init_offset) == payload_len
        print(entries)
        print("  + Parsing table section done")
        return entries

    def parse_memory_section(self, payload_len):
        print("  # Parsing memory section")
        init_offset = self.get_current_offset()
        count = self.readVarUint(32)
        entries = []
        for i in range(count):
            memtype = self.read_memory_type()
            entries.append(memtype)
        assert self.get_read_len(init_offset) == payload_len
        print(entries)
        print("  + Parsing memory section done")
        return entries

    def parse_global_section(self, payload_len):
        print("  # Parsing global section")
        init_offset = self.get_current_offset()
        count = self.readVarUint(32)
        globals = []
        for i in range(count):
            global_var = self.parse_global_variable()
            globals.append(global_var)
        assert self.get_read_len(init_offset) == payload_len
        print(globals)
        print("  + Parsing global section done")
        return globals

    def parse_global_variable(self):
        type = self.read_global_type()
        init = self.read_init_expr()
        return type, init

    def vui1PL(self):
        return self.readVarUint(1)

    def vui32PL(self):
        return self.readVarUint(32)

    def vui64PL(self):
        return self.readVarUint(64)

    def vi32PL(self):
        return self.readVarInt(32)

    def vi64PL(self):
        return self.readVarInt(64)

    def ui32PL(self):
        return self.readUInt(4)

    def ui64PL(self):
        return self.readUInt(8)

    def blockTypePL(self):
        val = self.readVarInt(7)
        return TypeConstructor(val)

    def brTablePL(self):
        target_count = self.readVarUint(32)
        target_table = []
        for i in range(target_count):
            entry = self.readVarUint(32)
            target_table.append(entry)
        default_target = self.readVarUint(32)
        return target_count, target_table, default_target

    def callIndPL(self):
        type_index = self.readVarUint(32)
        reserved = self.readVarUint(1)
        return type_index, reserved

    def memImmPL(self):
        flags = self.readVarUint(32)
        offset = self.readVarUint(32)
        return flags, offset

    class OpcodeFn:
        def __init__(self):
            self.fn_array = [None] * (0xbf + 1)

        def set(self, op, fn_tuple):
            idx = op.value
            self.fn_array[idx] = fn_tuple

        def get(self, op):
            return self.fn_array[op.value]

        def get_parser(self, op):
            entry = self.get(op)
            if entry is not None:
                return entry[0]
            return None

    def initOpcodeFn(self):
        self.opFn = self.OpcodeFn()

        self.opFn.set(Opcode.block, (self.blockTypePL,))
        self.opFn.set(Opcode.loop, (self.blockTypePL,))
        self.opFn.set(Opcode.if_, (self.blockTypePL,))
        self.opFn.set(Opcode.br, (self.vui32PL,))
        self.opFn.set(Opcode.br_if, (self.vui32PL,))
        self.opFn.set(Opcode.br_table, (self.brTablePL,))

        self.opFn.set(Opcode.call, (self.vui32PL,))
        self.opFn.set(Opcode.call_indirect, (self.callIndPL,))

        self.opFn.set(Opcode.get_local, (self.vui32PL,))
        self.opFn.set(Opcode.set_local, (self.vui32PL,))
        self.opFn.set(Opcode.tee_local, (self.vui32PL,))
        self.opFn.set(Opcode.get_global, (self.vui32PL,))
        self.opFn.set(Opcode.set_global, (self.vui32PL,))

        self.opFn.set(Opcode.i32_load, (self.memImmPL,))
        self.opFn.set(Opcode.i64_load, (self.memImmPL,))
        self.opFn.set(Opcode.f32_load, (self.memImmPL,))
        self.opFn.set(Opcode.f64_load, (self.memImmPL,))
        self.opFn.set(Opcode.i32_load8_s, (self.memImmPL,))
        self.opFn.set(Opcode.i32_load8_u, (self.memImmPL,))
        self.opFn.set(Opcode.i32_load16_s, (self.memImmPL,))
        self.opFn.set(Opcode.i32_load16_u, (self.memImmPL,))
        self.opFn.set(Opcode.i64_load8_s, (self.memImmPL,))
        self.opFn.set(Opcode.i64_load8_u, (self.memImmPL,))
        self.opFn.set(Opcode.i64_load16_s, (self.memImmPL,))
        self.opFn.set(Opcode.i64_load16_u, (self.memImmPL,))
        self.opFn.set(Opcode.i64_load32_s, (self.memImmPL,))
        self.opFn.set(Opcode.i64_load32_u, (self.memImmPL,))
        self.opFn.set(Opcode.i32_store, (self.memImmPL,))
        self.opFn.set(Opcode.i64_store, (self.memImmPL,))
        self.opFn.set(Opcode.f32_store, (self.memImmPL,))
        self.opFn.set(Opcode.f64_store, (self.memImmPL,))
        self.opFn.set(Opcode.i32_store8, (self.memImmPL,))
        self.opFn.set(Opcode.i32_store16, (self.memImmPL,))
        self.opFn.set(Opcode.i64_store8, (self.memImmPL,))
        self.opFn.set(Opcode.i64_store16, (self.memImmPL,))
        self.opFn.set(Opcode.i64_store32, (self.memImmPL,))
        self.opFn.set(Opcode.current_memory, (self.vui1PL,))
        self.opFn.set(Opcode.grow_memory, (self.vui1PL,))

        self.opFn.set(Opcode.i32_const, (self.vi32PL,))
        self.opFn.set(Opcode.i64_const, (self.vi64PL,))
        self.opFn.set(Opcode.f32_const, (self.ui32PL,))
        self.opFn.set(Opcode.f64_const, (self.ui64PL,))

    def read_opcode(self):
        byte = self.readUInt(1)
        op = Opcode(byte)
        payloadFn = self.opFn.get_parser(op)
        if payloadFn is None:
            return Op(op, None)
        else:
            return Op(op, payloadFn())

    def read_global_type(self):
        content_type = self.parse_value_type()
        mutability = self.readVarUint(1)
        return content_type, mutability

    def parse_export_section(self, payload_len):
        print("  # Parsing export section")
        init_offset = self.get_current_offset()
        count = self.readVarUint(32)
        entries = []
        for i in range(count):
            field_len = self.readVarUint(32)
            field_str = self.readUTF8(field_len)
            kind = ExternalKind(self.readUInt(1))
            index = self.readVarUint(32)
            entries.append((field_str, kind, index))
        assert self.get_read_len(init_offset) == payload_len
        print(entries)
        print("  + Parsing export section done")
        return entries

    def parse_start_section(self, payload_len):
        print("  # Parsing start section")
        index, len = self.readVarUintLen(32)
        assert len == payload_len
        print(index)
        print("  + Parsing start section done")
        return index

    def parse_element_section(self, payload_len):
        print("  # Parsing element section")
        init_offset = self.get_current_offset()
        count = self.readVarUint(32)
        entries = []
        for i in range(count):
            index = self.readVarUint(32)
            offset = self.read_init_expr()
            num_elem = self.readVarUint(32)
            elems = []
            for j in range(num_elem):
                elem = self.readVarUint(32)
                elems.append(elem)
            entry = (index, offset, num_elem, elems)
            entries.append(entry)
        assert self.get_read_len(init_offset) == payload_len
        print(entries)
        print("  + Parsing element section done")
        return entries

    def parse_code_section(self, payload_len):
        print("  # Parsing code section")
        init_offset = self.get_current_offset()
        count = self.readVarUint(32)
        bodies = []
        for i in range(count):
            body_size = self.readVarUint(32)
            body_head_offset = self.get_current_offset()
            local_count = self.readVarUint(32)
            locals = []
            for j in range(local_count):
                var_count = self.readVarUint(32)
                var_type = self.parse_value_type()
                local_entry = (var_count, var_type)
                locals.append(local_entry)
            body_head_size = self.get_read_len(body_head_offset)
            codelen = body_size - body_head_size - 1
            opcodes = []
            code_offset = self.get_current_offset()
            while self.get_read_len(code_offset) < codelen:
                opcode = self.read_opcode()
                opcodes.append(opcode)
            end = self.readUInt(1)
            assert end == Parser.endOpcode
            body = (locals, opcodes)
            print((locals, opcodes[:2], "etc."))
            bodies.append(body)
        assert self.get_read_len(init_offset) == payload_len
        print("  + Parsing code section done")
        return bodies

    def parse_data_section(self, payload_len):
        assert self.resData.name_section is None  # custom name section needs to be parsed after the data section!
        print("  # Parsing data section")
        init_offset = self.get_current_offset()
        count = self.readVarUint(32)
        entries = []
        for i in range(count):
            index = self.readVarUint(32)
            offset = self.read_init_expr()
            size = self.readVarUint(32)
            data = self.readBytes(size)
            entry = (index, offset, size, data)
            print("Data entry [len = {:d}] = {}...".format(size, data[:16]))
            entries.append(entry)
        assert self.get_read_len(init_offset) == payload_len
        print("  + Parsing data section done")
        return entries

    def parse(self):
        print("### Start Parsing WASM")
        self.parse_preamble()
        while not self.fileIsEof():
            self.parse_section()
        print("+++ Done Parsing WASM")
        return self.resData

#!/usr/bin/python3
import os
import enum


class VersionError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class type_constr(enum.Enum):
    def __repr__(self):
        return f"T<{self.name}>"

    i32 = 0x7f
    i64 = 0x7e
    f32 = 0x7d
    f64 = 0x7c
    anyfunc = 0x70
    func = 0x60
    empty_block = 0x40


class Opcode(enum.Enum):
    def __repr__(self):
        return f"Op<{self.name}>"

    #control flow operators
    unreachable = 0x00
    nop = 0x01
    block = 0x02
    loop = 0x03
    if_ = 0x04
    else_ = 0x05
    end = 0x0b
    br = 0x0c
    br_if = 0x0d
    br_table = 0x0e
    return_ = 0x0f

    # call operators
    call = 0x10
    call_indirect = 0x11

    # parametric operators
    drop = 0x1a
    select = 0x1b

    # variable access
    get_local = 0x20
    set_local = 0x21
    tee_local = 0x22
    get_global = 0x23
    set_global = 0x24

    # memory related operators
    i32_load = 0x28
    i64_load = 0x29
    f32_load = 0x2a
    f64_load = 0x2b
    i32_load8_s = 0x2c
    i32_load8_u = 0x2d
    i32_load16_s = 0x2e
    i32_load16_u = 0x2f
    i64_load8_s = 0x30
    i64_load8_u = 0x31
    i64_load16_s = 0x32
    i64_load16_u = 0x33
    i64_load32_s = 0x34
    i64_load32_u = 0x35
    i32_store = 0x36
    i64_store = 0x37
    f32_store = 0x38
    f64_store = 0x39
    i32_store8 = 0x3a
    i32_store16 = 0x3b
    i64_store8 = 0x3c
    i64_store16 = 0x3d
    i64_store32 = 0x3e
    current_memory = 0x3f
    grow_memory = 0x40

    # Constants
    i32_const = 0x41
    i64_const = 0x42
    f32_const = 0x43
    f64_const = 0x44

    # comparison operators
    i32_eqz = 0x45
    i32_eq = 0x46
    i32_ne = 0x47
    i32_lt_s = 0x48
    i32_lt_u = 0x49
    i32_gt_s = 0x4a
    i32_gt_u = 0x4b
    i32_le_s = 0x4c
    i32_le_u = 0x4d
    i32_ge_s = 0x4e
    i32_ge_u = 0x4f
    i64_eqz = 0x50
    i64_eq = 0x51
    i64_ne = 0x52
    i64_lt_s = 0x53
    i64_lt_u = 0x54
    i64_gt_s = 0x55
    i64_gt_u = 0x56
    i64_le_s = 0x57
    i64_le_u = 0x58
    i64_ge_s = 0x59
    i64_ge_u = 0x5a
    f32_eq = 0x5b
    f32_ne = 0x5c
    f32_lt = 0x5d
    f32_gt = 0x5e
    f32_le = 0x5f
    f32_ge = 0x60
    f64_eq = 0x61
    f64_ne = 0x62
    f64_lt = 0x63
    f64_gt = 0x64
    f64_le = 0x65
    f64_ge = 0x66

    # numeric operators
    i32_clz = 0x67
    i32_ctz = 0x68
    i32_popcnt = 0x69
    i32_add = 0x6a
    i32_sub = 0x6b
    i32_mul = 0x6c
    i32_div_s = 0x6d
    i32_div_u = 0x6e
    i32_rem_s = 0x6f
    i32_rem_u = 0x70
    i32_and = 0x71
    i32_or = 0x72
    i32_xor = 0x73
    i32_shl = 0x74
    i32_shr_s = 0x75
    i32_shr_u = 0x76
    i32_rotl = 0x77
    i32_rotr = 0x78
    i64_clz = 0x79
    i64_ctz = 0x7a
    i64_popcnt = 0x7b
    i64_add = 0x7c
    i64_sub = 0x7d
    i64_mul = 0x7e
    i64_div_s = 0x7f
    i64_div_u = 0x80
    i64_rem_s = 0x81
    i64_rem_u = 0x82
    i64_and = 0x83
    i64_or = 0x84
    i64_xor = 0x85
    i64_shl = 0x86
    i64_shr_s = 0x87
    i64_shr_u = 0x88
    i64_rotl = 0x89
    i64_rotr = 0x8a
    f32_abs = 0x8b
    f32_neg = 0x8c
    f32_ceil = 0x8d
    f32_floor = 0x8e
    f32_trunc = 0x8f
    f32_nearest = 0x90
    f32_sqrt = 0x91
    f32_add = 0x92
    f32_sub = 0x93
    f32_mul = 0x94
    f32_div = 0x95
    f32_min = 0x96
    f32_max = 0x97
    f32_copysign = 0x98
    f64_abs = 0x99
    f64_neg = 0x9a
    f64_ceil = 0x9b
    f64_floor = 0x9c
    f64_trunc = 0x9d
    f64_nearest = 0x9e
    f64_sqrt = 0x9f
    f64_add = 0xa0
    f64_sub = 0xa1
    f64_mul = 0xa2
    f64_div = 0xa3
    f64_min = 0xa4
    f64_max = 0xa5
    f64_copysign = 0xa6

    # conversions
    i32_wrap_i64 = 0xa7
    i32_trunc_s_f32 = 0xa8
    i32_trunc_u_f32 = 0xa9
    i32_trunc_s_f64 = 0xaa
    i32_trunc_u_f64 = 0xab
    i64_extend_s_i32 = 0xac
    i64_extend_u_i32 = 0xad
    i64_trunc_s_f32 = 0xae
    i64_trunc_u_f32 = 0xaf
    i64_trunc_s_f64 = 0xb0
    i64_trunc_u_f64 = 0xb1
    f32_convert_s_i32 = 0xb2
    f32_convert_u_i32 = 0xb3
    f32_convert_s_i64 = 0xb4
    f32_convert_u_i64 = 0xb5
    f32_demote_f64 = 0xb6
    f64_convert_s_i32 = 0xb7
    f64_convert_u_i32 = 0xb8
    f64_convert_s_i64 = 0xb9
    f64_convert_u_i64 = 0xba
    f64_promote_f32 = 0xbb

    # reinterpretations
    i32_reinterpret_f32 = 0xbc
    i64_reinterpret_f64 = 0xbd
    f32_reinterpret_i32 = 0xbe
    f64_reinterpret_i64 = 0xbf


class Op:
        def __init__(self, opcode, payload):
            self.opcode = opcode
            self.payload = payload

        def __repr__(self):
            return f"{self.opcode.name}" + (f"<{self.payload}>" if self.payload is not None else "")


class external_kind(enum.Enum):
    def __repr__(self):
        return f"Ext<{self.name}>"

    Function = 0
    Table = 1
    Memory = 2
    Global = 3


class ParseData:
    def __init__(self):
        self.custom_sections = []
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
        self.initOpcodeFn()


    def read_type_constr(self):
        byte, l = self.readVarInt(7)
        type_c = type_constr(byte)
        return type_c, l

    def fileIsEof(self):
        file_len = os.fstat(self.file.fileno()).st_size
        return self.file.tell() == file_len

    def readUInt(self,l):
        return int.from_bytes(self.file.read(l), byteorder='little')

    def readVarUint(self,l):
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
        return res, len

    def readVarInt(self,l):
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
        return res, len

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
        global data
        print(" ## Parsing section ...", end="")
        sec_id, _ = self.readVarUint(7)
        payload_len, _ = self.readVarUint(32)
        name_len_size = 0
        name_bytes = bytes()
        name = ""
        if sec_id == 0:
            name_len, name_len_size = self.readVarUint(32)
            name_bytes = self.file.read(name_len)
            name = name_bytes.decode("utf-8")
            print ("[name = '%s']" % name)
        else:
            print ("[id = %d]" % sec_id)
        payload_data_len = payload_len - len(name_bytes) - name_len_size
        if sec_id == 0x0:
            self.resData.custom_sections.append(self.parse_custom_section(name, payload_data_len))
        elif sec_id == 0x1:
            self.resData.type_section = self.parse_type_section(name, payload_data_len)
        elif sec_id == 0x2:
            self.resData.import_section = self.parse_import_section(name, payload_data_len)
        elif sec_id == 0x3:
            self.resData.function_section = self.parse_function_section(name, payload_data_len)
        elif sec_id == 0x4:
            self.resData.table_section = self.parse_table_section(name, payload_data_len)
        elif sec_id == 0x5:
            self.resData.memory_section = self.parse_memory_section(name, payload_data_len)
        elif sec_id == 0x6:
            self.resData.global_section = self.parse_global_section(name, payload_data_len)
        elif sec_id == 0x7:
            self.resData.export_section = self.parse_export_section(name, payload_data_len)
        elif sec_id == 0x8:
            self.resData.start_section = self.parse_start_section(name, payload_data_len)
        elif sec_id == 0x9:
            self.resData.element_section = self.parse_element_section(name, payload_data_len)
        elif sec_id == 0xA:
            self.resData.code_section = self.parse_code_section(name, payload_data_len)
        elif sec_id == 0xB:
            self.resData.data_section = self.parse_data_section(name, payload_data_len)
        else:
            raise Exception("Unknown Section ID" + str(sec_id))
        print(" ++ Done parsing section")

    def parse_custom_section(self, name, payload_len):
        print("  # Parsing custom section")
        payload = self.file.read(payload_len)
        print("Custom Section Data [len={:d}] = {}...".format(payload_len, payload[:32]))
        print("  + Parsing custom section done")
        return payload

    def parse_import_section(self, name, payload_len):
        print("  # Parsing import section")
        total_len = 0
        count, l = self.readVarUint(32)
        total_len += l
        entries = []
        for i in range(count):
            module_len, l = self.readVarUint(32)
            total_len += l
            module_str_bytes = self.file.read(module_len)
            total_len += module_len
            module_str = module_str_bytes.decode("utf-8")
            field_len, l = self.readVarUint(32)
            total_len += l
            field_str_bytes = self.file.read(field_len)
            total_len += field_len
            field_str = field_str_bytes.decode("utf-8")
            kind = external_kind(self.readUInt(1))
            total_len += 1
            if kind == external_kind.Function:
                type, l = self.readVarUint(32)
                total_len += l
            elif kind == external_kind.Table:
                type, l = self.parse_table_type()
                total_len += l
            elif kind == external_kind.Memory:
                type, l = self.parse_memory_type()
                total_len += l
            elif kind == external_kind.Global:
                type, l = self.parse_global_type()
                total_len += l
            else:
                assert False
            import_entry = (module_str, field_str, kind)
            entries.append(import_entry)
        assert total_len == payload_len
        print(entries)
        print("  + Parsing import section done")
        return entries

    def parse_type_section(self, name, payload_len):
        print("  # Parsing type section")
        total_len = 0
        count, l = self.readVarUint(32)
        total_len += l
        types = []
        while total_len < payload_len:
            fnType, l = self.read_fn_type()
            total_len += l
            types.append(fnType)
        assert total_len == payload_len
        print(types)
        print("  + Parsing type section done")
        return types


    def read_fn_type(self):
        total_len = 0
        form, l = self.read_type_constr()
        total_len += l
        param_count, l = self.readVarUint(32)
        total_len += l
        param_types = []
        for i in range(param_count):
            param_type, l = self.parse_value_type()
            total_len += l
            param_types.append(param_type)
        return_count, l = self.readVarUint(1)
        total_len += l
        return_types = []
        for i in range(return_count):
            return_type, l = self.parse_value_type()
            total_len += l
            return_types.append(return_type)
        return (form, param_types, return_types), total_len


    def parse_value_type(self):
        ptype, l = self.readVarUint(7)
        param_type = type_constr(ptype)
        return param_type, l


    def parse_function_section(self, name, payload_len):
        print("  # Parsing function section")
        total_len = 0
        count, l = self.readVarUint(32)
        total_len += l
        types = []
        for i in range(count):
            type, l = self.readVarUint(32)
            total_len += l
            types.append(type)
        assert total_len == payload_len
        print(types)
        print("  + Parsing function section done")
        return types


    def parse_table_section(self, name, payload_len):
        print("  # Parsing table section")
        total_len = 0
        count, l = self.readVarUint(32)
        total_len += l
        entries = []
        for i in range(count):
            entry, l = self.parse_table_type()
            total_len += l
            entries.append(entry)
        assert total_len == payload_len
        print(entries)
        print("  + Parsing table section done")
        return entries

    def parse_table_type(self):
        total_len = 0
        elem_type, l = self.readVarUint(7)
        total_len += l
        limits, l = self.parse_resizable_limits()
        total_len += l
        entry = (elem_type, limits)
        return entry, total_len

    def parse_resizable_limits(self):
        total_len = 0
        limits_flag, l = self.readVarUint(1)
        total_len += l
        limits_initial, l = self.readVarUint(32)
        total_len += l
        if limits_flag == 1:
            limits_maximum, l = self.readVarUint(32)
            total_len += l
        else:
            limits_maximum = None
        limits = (limits_flag, limits_initial, limits_maximum)
        return limits, total_len

    def parse_memory_section(self, name, payload_len):
        print("  # Parsing memory section")
        total_len = 0
        count, l = self.readVarUint(32)
        total_len += l
        entries = []
        for i in range(count):
            memtype, l = self.parse_memory_type()
            total_len += l
            entries.append(memtype)
        assert total_len == payload_len
        print(entries)
        print("  + Parsing memory section done")
        return entries

    def parse_memory_type(self):
        return self.parse_resizable_limits()

    def parse_global_section(self, name, payload_len):
        print("  # Parsing global section")
        total_len = 0
        count, l = self.readVarUint(32)
        total_len += l
        globals = []
        for i in range(count):
            global_var, l = self.parse_global_variable()
            total_len += l
            globals.append(global_var)
        assert total_len == payload_len
        print(globals)
        print("  + Parsing global section done")
        return globals

    def parse_global_variable(self):
        total_len = 0
        type, l = self.parse_global_type()
        total_len += l
        init, l = self.parse_init_expr()
        total_len += l
        return (type, init), total_len

    def parse_init_expr(self):
        op, l = self.parse_opcode()
        res = self.readUInt(1)
        if res != 0x0b:
            print("oops")
        assert res == 0x0b
        return op, l + 1


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
        return self.readUInt(4), 4


    def ui64PL(self):
        return self.readUInt(8), 8


    def blockTypePL(self):
        return self.readVarInt(7)


    def brTablePL(self):
        total_len = 0
        target_count, l = self.readVarUint(32)
        total_len += l
        target_table = []
        for i in range(target_count):
            entry, l = self.readVarUint(32)
            total_len += l
            target_table.append(entry)
        default_target, l = self.readVarUint(32)
        total_len += l
        return (target_count, target_table, default_target), total_len

    def callIndPL(self):
        total_len = 0
        type_index, l = self.readVarUint(32)
        total_len += l
        reserved, l = self.readVarUint(1)
        total_len += l
        return (type_index, reserved), total_len

    def memImmPL(self):
        total_len = 0
        flags, l = self.readVarUint(32)
        total_len += l
        offset, l = self.readVarUint(32)
        total_len += l
        return (flags, offset), total_len

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

    def makePayload(self, op, parser):
        payload, len = parser()
        return Op(op, payload), 1 + len

    def parse_opcode(self, file=None):
        byte = self.readUInt(1)
        op = Opcode(byte)
        payloadFn = self.opFn.get_parser(op)
        if payloadFn is None:
            return Op(op, None), 1
        else:
            return self.makePayload(op, payloadFn)

    def parse_global_type(self):
        total_len = 0
        content_type, l = self.parse_value_type()
        total_len += l
        mutability, l = self.readVarUint(1)
        total_len += l
        return (content_type, mutability), total_len


    def parse_export_section(self, name, payload_len):
        print("  # Parsing export section")
        total_len = 0
        count, l = self.readVarUint(32)
        total_len += l
        entries = []
        for i in range(count):
            field_len, l = self.readVarUint(32)
            total_len += l
            field_str_bytes = self.file.read(field_len)
            total_len += field_len
            field_str = field_str_bytes.decode("utf-8")
            kind = external_kind(self.readUInt(1))
            total_len += 1
            index, l = self.readVarUint(32)
            entries.append((field_str, kind, index))
        assert total_len <= payload_len # TODO what about remaining bytes?
        print(entries)
        print("  + Parsing export section done")
        return entries


    def parse_start_section(self, name, payload_len):
        print("  # Parsing start section")
        index, l = self.readVarUint(32)
        assert l == payload_len
        print(index)
        print("  + Parsing start section done")
        return index


    def parse_element_section(self, name, payload_len):
        print("  # Parsing element section")
        total_len = 0
        count, l = self.readVarUint(32)
        total_len += l
        entries = []
        for i in range(count):
            index, l = self.readVarUint(32)
            total_len += l
            offset, l = self.parse_init_expr()
            total_len += l
            num_elem, l = self.readVarUint(32)
            total_len += l
            elems = []
            for i in range(num_elem):
                elem, l = self.readVarUint(32)
                total_len += l
                elems.append(elem)
            entry = (index, offset, num_elem, elems)
            entries.append(entry)
        assert total_len == payload_len
        print(entries)
        print("  + Parsing element section done")
        return entries

    def parse_code_section(self, name, payload_len):
        print("  # Parsing code section")
        total_len = 0
        count, l = self.readVarUint(32)
        total_len += l
        bodies = []
        for i in range(count):
            body_head_size = 0
            body_size, size_l = self.readVarUint(32)
            total_len += size_l
            local_count, l = self.readVarUint(32)
            body_head_size += l
            locals = []
            for j in range(local_count):
                var_count, l = self.readVarUint(32)
                body_head_size += l
                var_type, l = self.parse_value_type()
                body_head_size += l
                local_entry = (var_count, var_type)
                locals.append(local_entry)
            total_len += body_head_size
            codelen = body_size - body_head_size - 1
            opcodes = []
            readlen = 0
            while readlen < codelen:
                opcode, l = self.parse_opcode()
                readlen += l
                opcodes.append(opcode)
            total_len += readlen
            end = self.readUInt(1)
            total_len += 1
            assert end == Parser.endOpcode
            body = (locals, opcodes)
            print((locals, opcodes[:2], "etc."))
            bodies.append(body)
        assert total_len == payload_len
        print("  + Parsing code section done")
        return bodies

    def parse_data_section(self, name, payload_len):
        print("  # Parsing data section")
        total_len = 0
        count, l = self.readVarUint(32)
        total_len += l
        entries = []
        for i in range(count):
            index, l = self.readVarUint(32)
            total_len += l
            offset, l = self.parse_init_expr()
            total_len += l
            size, l = self.readVarUint(32)
            total_len += l
            data = self.file.read(size)
            total_len += size
            entry = (index, offset, size, data)
            print("Data entry [len = {:d}] = {}...".format(size, data[:16]))
            entries.append(entry)
        assert total_len == payload_len
        print("  + Parsing data section done")
        return entries

    def parse(self):
        print("### Start Parsing WASM")
        self.parse_preamble()
        while not self.fileIsEof():
            self.parse_section()
        print("+++ Done Parsing WASM")
        return self.resData

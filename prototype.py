#!/usr/bin/python3
import sys
import os
import enum
import io

magic_num = 0x6d736100
supported_version = 0x1
endOpcode = 0x0b


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

def read_type_constr(f):
    byte, l = readVarInt(f, 7)
    type_c = type_constr(byte)
    return type_c, l


class Opcode(enum.Enum):
    def __repr__(self):
        return f"Op<{self.name}>"

    #control flow operators
    unreachable = 0x00
    nop = 0x01
    block = 0x02
    loop = 0x03
    _if = 0x04
    _else = 0x05
    end = 0x0b
    br = 0x0c
    br_if = 0x0d
    br_table = 0x0e
    _return = 0x0f

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

class external_kind(enum.Enum):
    def __repr__(self):
        return f"Ext<{self.name}>"

    Function = 0
    Table = 1
    Memory = 2
    Global = 3


def fileIsEof(f):
    file_len = os.fstat(f.fileno()).st_size
    return f.tell() == file_len


def readUInt(f, l):
    return int.from_bytes(f.read(l), byteorder='little')


def readVarUint(f, l):
    res = 0
    shift = 0
    len = 0
    while True:
        len += 1
        byte = readUInt(f, 1)
        res |= (0x7f & byte) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
    return res, len


def readVarInt(f, l):
    res = 0
    shift = 0
    size = 0
    len = 0
    while True:
        len += 1
        byte = readUInt(f, 1)
        res |= (0x7f & byte) << shift
        shift += 7
        if (byte & 0x80) == 0:
            break
    if shift < size and (byte & 0x40) != 0:
        res |= (~0 << shift)
    return res, len


def parse_preamble(f):
    print("Parsing WASM header ...", end="")
    magic = readUInt(f, 4)
    if magic != magic_num:
        print("%02x != %02x" % (magic, magic_num))
        raise Exception("not a wasm file!")
    version = readUInt(f, 4)
    if version != supported_version:
        raise VersionError("only version 1 is supported currently")
    print(" OK")


class Data:
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

data = Data()


def parse_section(f):
    global data
    print(" ## Parsing section ...", end="")
    sec_id, _ = readVarUint(f, 7)
    payload_len, _ = readVarUint(f, 32)
    name_len_size = 0
    name_bytes = bytes()
    name = ""
    if sec_id == 0:
        name_len, name_len_size = readVarUint(f, 32)
        name_bytes = f.read(name_len)
        name = name_bytes.decode("utf-8")
        print ("[name = '%s']" % name)
    else:
        print ("[id = %d]" % sec_id)
    payload_data_len = payload_len - len(name_bytes) - name_len_size
    if sec_id == 0x0:
        data.custom_sections.append(parse_custom_section(name, f, payload_data_len))
    elif sec_id == 0x1:
        data.type_section = parse_type_section(name, f, payload_data_len)
    elif sec_id == 0x2:
        data.import_section = parse_import_section(name, f, payload_data_len)
    elif sec_id == 0x3:
        data.function_section = parse_function_section(name, f, payload_data_len)
    elif sec_id == 0x4:
        data.table_section = parse_table_section(name, f, payload_data_len)
    elif sec_id == 0x5:
        data.memory_section = parse_memory_section(name, f, payload_data_len)
    elif sec_id == 0x6:
        data.global_section = parse_global_section(name, f, payload_data_len)
    elif sec_id == 0x7:
        data.export_section = parse_export_section(name, f, payload_data_len)
    elif sec_id == 0x8:
        data.start_section = parse_start_section(name, f, payload_data_len)
    elif sec_id == 0x9:
        data.element_section = parse_element_section(name, f, payload_data_len)
    elif sec_id == 0xA:
        data.code_section = parse_code_section(name, f, payload_data_len)
    elif sec_id == 0xB:
        data.data_section = parse_data_section(name, f, payload_data_len)
    else:
        raise Exception("Unknown Section ID" + str(sec_id))
    print(" ++ Done parsing section")


def parse_custom_section(name, f, payload_len):
    print("  # Parsing custom section")
    payload = f.read(payload_len)
    print("Custom Section Data [len={:d}] = {}...".format(payload_len, payload[:32]))
    print("  + Parsing custom section done")
    return payload


def parse_import_section(name, f, payload_len):
    print("  # Parsing import section")
    total_len = 0
    count, l = readVarUint(f, 32)
    total_len += l
    entries = []
    for i in range(count):
        module_len, l = readVarUint(f, 32)
        total_len += l
        module_str_bytes = f.read(module_len)
        total_len += module_len
        module_str = module_str_bytes.decode("utf-8")
        field_len, l = readVarUint(f, 32)
        total_len += l
        field_str_bytes = f.read(field_len)
        total_len += field_len
        field_str = field_str_bytes.decode("utf-8")
        kind = external_kind(readUInt(f, 1))
        total_len += 1
        if kind == external_kind.Function:
            type, l = readVarUint(f, 32)
            total_len += l
        elif kind == external_kind.Table:
            type, l = parse_table_type(f)
            total_len += l
        elif kind == external_kind.Memory:
            type, l = parse_memory_type(f)
            total_len += l
        elif kind == external_kind.Global:
            type, l = parse_global_type(f)
            total_len += l
        else:
            assert False
        import_entry = (module_str, field_str, kind)
        entries.append(import_entry)
    assert total_len == payload_len
    print(entries)
    print("  + Parsing import section done")
    return entries


def parse_type_section(name, f, payload_len):
    print("  # Parsing type section")
    total_len = 0
    count, l = readVarUint(f, 32)
    total_len += l
    types = []
    while total_len < payload_len:
        fnType, l = read_fn_type(f)
        total_len += l
        types.append(fnType)
    assert total_len == payload_len
    print(types)
    print("  + Parsing type section done")
    return types


def read_fn_type(f):
    total_len = 0
    form, l = read_type_constr(f)
    total_len += l
    param_count, l = readVarUint(f, 32)
    total_len += l
    param_types = []
    for i in range(param_count):
        param_type, l = parse_value_type(f)
        total_len += l
        param_types.append(param_type)
    return_count, l = readVarUint(f, 1)
    total_len += l
    return_types = []
    for i in range(return_count):
        return_type, l = parse_value_type(f)
        total_len += l
        return_types.append(return_type)
    return (form, param_types, return_types), total_len


def parse_value_type(f):
    ptype, l = readVarUint(f, 7)
    param_type = type_constr(ptype)
    return param_type, l


def parse_function_section(name, f, payload_len):
    print("  # Parsing function section")
    total_len = 0
    count, l = readVarUint(f, 32)
    total_len += l
    types = []
    for i in range(count):
        type, l = readVarUint(f, 32)
        total_len += l
        types.append(type)
    assert total_len == payload_len
    print(types)
    print("  + Parsing function section done")
    return types


def parse_table_section(name, f, payload_len):
    print("  # Parsing table section")
    total_len = 0
    count, l = readVarUint(f, 32)
    total_len += l
    entries = []
    for i in range(count):
        entry, l = parse_table_type(f)
        total_len += l
        entries.append(entry)
    assert total_len == payload_len
    print(entries)
    print("  + Parsing table section done")
    return entries

def parse_table_type(f):
    total_len = 0
    elem_type, l = readVarUint(f, 7)
    total_len += l
    limits, l = parse_resizable_limits(f)
    total_len += l
    entry = (elem_type, limits)
    return entry, total_len


def parse_resizable_limits(f):
    total_len = 0
    limits_flag, l = readVarUint(f, 1)
    total_len += l
    limits_initial, l = readVarUint(f, 32)
    total_len += l
    if limits_flag == 1:
        limits_maximum, l = readVarUint(f, 32)
        total_len += l
    else:
        limits_maximum = None
    limits = (limits_flag, limits_initial, limits_maximum)
    return limits, total_len


def parse_memory_section(name, f, payload_len):
    print("  # Parsing memory section")
    total_len = 0
    count, l = readVarUint(f, 32)
    total_len += l
    entries = []
    for i in range(count):
        memtype, l = parse_memory_type(f)
        total_len += l
        entries.append(memtype)
    assert total_len == payload_len
    print(entries)
    print("  + Parsing memory section done")
    return entries


def parse_memory_type(f):
    return parse_resizable_limits(f)


def parse_global_section(name, f, payload_len):
    print("  # Parsing global section")
    total_len = 0
    count, l = readVarUint(f, 32)
    total_len += l
    globals = []
    for i in range(count):
        global_var, l = parse_global_variable(f)
        total_len += l
        globals.append(global_var)
    assert total_len == payload_len
    print(globals)
    print("  + Parsing global section done")
    return globals


def parse_global_variable(f):
    total_len = 0
    type, l = parse_global_type(f)
    total_len += l
    init, l = parse_init_expr(f)
    total_len += l
    return (type, init), total_len


def parse_init_expr(f):
    op, l = parse_opcode(f)
    res = readUInt(f, 1)
    if res != 0x0b:
        print("oops")
    assert res == 0x0b
    return op, l + 1


def TODO(f):
    raise Exception("IMPLEMENT PAYLOAD PARSING")


def vui1PL(f):
    return readVarUint(f, 1)


def vui32PL(f):
    return readVarUint(f, 32)


def vui64PL(f):
    return readVarUint(f, 64)

def vi32PL(f):
    return readVarInt(f, 32)


def vi64PL(f):
    return readVarInt(f, 64)


def ui32PL(f):
    return readUInt(f, 4), 4


def ui64PL(f):
    return readUInt(f, 8), 8


def blockTypePL(f):
    return readVarInt(f, 7)


def brTablePL(f):
    total_len = 0
    target_count, l = readVarUint(f, 32)
    total_len += l
    target_table = []
    for i in range(target_count):
        entry, l = readVarUint(f, 32)
        total_len += l
        target_table.append(entry)
    default_target, l = readVarUint(f, 32)
    total_len += l
    return (target_count, target_table, default_target), total_len


def callIndPL(f):
    total_len = 0
    type_index, l = readVarUint(f, 32)
    total_len += l
    reserved, l = readVarUint(f, 1)
    total_len += l
    return (type_index, reserved), total_len


def memImmPL(f):
    total_len = 0
    flags, l = readVarUint(f, 32)
    total_len += l
    offset, l = readVarUint(f, 32)
    total_len += l
    return (flags, offset), total_len


class Op:
    def __init__(self, opcode, payload):
        self.opcode = opcode
        self.payload = payload

    def __repr__(self):
        return f"{self.opcode.name}" + (f"<{self.payload}>" if self.payload is not None else "")


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


opFn = OpcodeFn()

opFn.set(Opcode.block, (blockTypePL,))
opFn.set(Opcode.loop, (blockTypePL,))
opFn.set(Opcode._if, (blockTypePL,))
opFn.set(Opcode.br, (vui32PL,))
opFn.set(Opcode.br_if, (vui32PL,))
opFn.set(Opcode.br_table, (brTablePL,))

opFn.set(Opcode.call, (vui32PL,))
opFn.set(Opcode.call_indirect, (callIndPL,))

opFn.set(Opcode.get_local, (vui32PL,))
opFn.set(Opcode.set_local, (vui32PL,))
opFn.set(Opcode.tee_local, (vui32PL,))
opFn.set(Opcode.get_global, (vui32PL,))
opFn.set(Opcode.set_global, (vui32PL,))

opFn.set(Opcode.i32_load, (memImmPL,))
opFn.set(Opcode.i64_load, (memImmPL,))
opFn.set(Opcode.f32_load, (memImmPL,))
opFn.set(Opcode.f64_load, (memImmPL,))
opFn.set(Opcode.i32_load8_s, (memImmPL,))
opFn.set(Opcode.i32_load8_u, (memImmPL,))
opFn.set(Opcode.i32_load16_s, (memImmPL,))
opFn.set(Opcode.i32_load16_u, (memImmPL,))
opFn.set(Opcode.i64_load8_s, (memImmPL,))
opFn.set(Opcode.i64_load8_u, (memImmPL,))
opFn.set(Opcode.i64_load16_s, (memImmPL,))
opFn.set(Opcode.i64_load16_u, (memImmPL,))
opFn.set(Opcode.i64_load32_s, (memImmPL,))
opFn.set(Opcode.i64_load32_u, (memImmPL,))
opFn.set(Opcode.i32_store, (memImmPL,))
opFn.set(Opcode.i64_store, (memImmPL,))
opFn.set(Opcode.f32_store, (memImmPL,))
opFn.set(Opcode.f64_store, (memImmPL,))
opFn.set(Opcode.i32_store8, (memImmPL,))
opFn.set(Opcode.i32_store16, (memImmPL,))
opFn.set(Opcode.i64_store8, (memImmPL,))
opFn.set(Opcode.i64_store16, (memImmPL,))
opFn.set(Opcode.i64_store32, (memImmPL,))
opFn.set(Opcode.current_memory, (vui1PL,))
opFn.set(Opcode.grow_memory, (vui1PL,))

opFn.set(Opcode.i32_const, (vi32PL,))
opFn.set(Opcode.i64_const, (vi64PL,))
opFn.set(Opcode.f32_const, (ui32PL,))
opFn.set(Opcode.f64_const, (ui64PL,))


def makePayload(op, parser, f):
    payload, len = parser(f)
    return Op(op, payload), 1 + len

def parse_opcode(f):
    byte = readUInt(f, 1)
    op = Opcode(byte)
    payloadFn = opFn.get_parser(op)
    if payloadFn is None:
        return Op(op, None), 1
    else:
        return makePayload(op, payloadFn, f)


def parse_global_type(f):
    total_len = 0
    content_type, l = parse_value_type(f)
    total_len += l
    mutability, l = readVarUint(f, 1)
    total_len += l
    return (content_type, mutability), total_len


def parse_export_section(name, f, payload_len):
    print("  # Parsing export section")
    total_len = 0
    count, l = readVarUint(f, 32)
    total_len += l
    entries = []
    for i in range(count):
        field_len, l = readVarUint(f, 32)
        total_len += l
        field_str_bytes = f.read(field_len)
        total_len += field_len
        field_str = field_str_bytes.decode("utf-8")
        kind = external_kind(readUInt(f, 1))
        total_len += 1
        index, l = readVarUint(f, 32)
        entries.append((field_str, kind, index))
    assert total_len <= payload_len # TODO what about remaining bytes?
    print(entries)
    print("  + Parsing export section done")
    return entries


def parse_start_section(name, f, payload_len):
    print("  # Parsing start section")
    index, l = readVarUint(f, 32)
    assert l == payload_len
    print(index)
    print("  + Parsing start section done")
    return index


def parse_element_section(name, f, payload_len):
    print("  # Parsing element section")
    total_len = 0
    count, l = readVarUint(f, 32)
    total_len += l
    entries = []
    for i in range(count):
        index, l = readVarUint(f, 32)
        total_len += l
        offset, l = parse_init_expr(f)
        total_len += l
        num_elem, l = readVarUint(f, 32)
        total_len += l
        elems = []
        for i in range(num_elem):
            elem, l = readVarUint(f, 32)
            total_len += l
            elems.append(elem)
        entry = (index, offset, num_elem, elems)
        entries.append(entry)
    assert total_len == payload_len
    print(entries)
    print("  + Parsing element section done")
    return entries


def parse_code_section(name, f, payload_len):
    print("  # Parsing code section")
    total_len = 0
    count, l = readVarUint(f, 32)
    total_len += l
    bodies = []
    for i in range(count):
        body_head_size = 0
        body_size, size_l = readVarUint(f, 32)
        total_len += size_l
        local_count, l = readVarUint(f, 32)
        body_head_size += l
        locals = []
        for j in range(local_count):
            var_count, l = readVarUint(f, 32)
            body_head_size += l
            var_type, l = parse_value_type(f)
            body_head_size += l
            local_entry = (var_count, var_type)
            locals.append(local_entry)
        total_len += body_head_size
        codelen = body_size - body_head_size - 1
        code = f.read(codelen)
        #total_len += codelen
        end = readUInt(f, 1)
        total_len += 1
        assert end == endOpcode
        code_file = io.BytesIO(code)
        opcodes = []
        while code_file.tell() != len(code):
            opcode, l = parse_opcode(code_file)
            total_len += l
            opcodes.append(opcode)
        body = (locals, opcodes)
        print((locals, opcodes[:2], "etc."))
        bodies.append(body)
    assert total_len == payload_len
    print("  + Parsing code section done")
    return bodies


def parse_data_section(name, f, payload_len):
    print("  # Parsing data section")
    total_len = 0
    count, l = readVarUint(f, 32)
    total_len += l
    entries = []
    for i in range(count):
        index, l = readVarUint(f, 32)
        total_len += l
        offset, l = parse_init_expr(f)
        total_len += l
        size, l = readVarUint(f, 32)
        total_len += l
        data = f.read(size)
        total_len += size
        entry = (index, offset, size, data)
        print("Data entry [len = {:d}] = {}...".format(size, data[:16]))
        entries.append(entry)
    assert total_len == payload_len
    print("  + Parsing data section done")
    return entries


def parse(f):
    print("### Start Parsing WASM")
    parse_preamble(f)
    while not fileIsEof(f):
        parse_section(f)
    print("+++ Done Parsing WASM")

class Function:
    def __init__(self, type, body):
        self.type = type
        self.body = body

    def __repr__(self):
        return f"<FN type:{self.type} body: {self.body}>"

def createStructures():
    global data
    assert len(data.function_section) == len(data.code_section)
    fns = data.function_section
    types = data.type_section
    bodies = data.code_section
    functions = []
    for i in range(len(data.function_section)):
        fn_type_idx = fns[i]
        fn_type = types[fn_type_idx]
        assert fn_type[0] == type_constr.func or fn_type[0] == type_constr.anyfunc
        fn_body = bodies[i]
        fn = Function(fn_type, fn_body)
        functions.append(fn)
    for fn in functions:
        print(fn)


def runMain():
    pass


def main():
    filename = sys.argv[1]
    with open(filename, "rb") as f:
        parse(f)
    createStructures()
    if data.start_section is not None:
        runMain()

main()

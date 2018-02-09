#!/usr/bin/python3
import sys
import os
import enum

magic_num = 0x6d736100
supported_version = 0x1
endOpcode = 0x0b


class VersionError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class value_type(enum.Enum):
    i32 = 0x7f
    i64 = 0x7e
    f32 = 0x7d
    f64 = 0x7c
    anyfunc = 0x70
    func = 0x60
    empty_block = 0x40

class external_kind(enum.Enum):
    Function = 0
    Table = 1
    Memory = 2
    Global = 3


class Opcode(enum.Enum):
    unreachable = 0x00
    nop = 0x01
    # ...
    end = 0x0b
    # ...
    get_global = 0x23
    # ...
    i32_const = 0x41
    i64_const = 0x42
    f32_const = 0x43
    f64_const = 0x44


def test(f):
    while True:
        chunk = f.read(4)
        if chunk:
            print(chunk)
        else:
            break


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
        byte = int.from_bytes(f.read(1), byteorder="little")
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
        byte = int.from_bytes(f.read(1), byteorder="little")
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


def parse_section(f):
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
        parse_custom_section(name, f, payload_data_len)
    elif sec_id == 0x1:
        parse_type_section(name, f, payload_data_len)
    elif sec_id == 0x2:
        parse_import_section(name, f, payload_data_len)
    elif sec_id == 0x3:
        parse_function_section(name, f, payload_data_len)
    elif sec_id == 0x4:
        parse_table_section(name, f, payload_data_len)
    elif sec_id == 0x5:
        parse_memory_section(name, f, payload_data_len)
    elif sec_id == 0x6:
        parse_global_section(name, f, payload_data_len)
    elif sec_id == 0x7:
        parse_export_section(name, f, payload_data_len)
    elif sec_id == 0x8:
        parse_start_section(name, f, payload_data_len)
    elif sec_id == 0x9:
        parse_element_section(name, f, payload_data_len)
    elif sec_id == 0xA:
        parse_code_section(name, f, payload_data_len)
    elif sec_id == 0xB:
        parse_data_section(name, f, payload_data_len)
    else:
        raise Exception("Unknown Section ID" + str(sec_id))
    print(" ++ Done parsing section")


def parse_custom_section(name, f, payload_len):
    print("  # Parsing custom section")
    payload = f.read(payload_len)
    print(payload)
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
    count, len = readVarUint(f, 32)
    payload_len -= len
    types = []
    while payload_len > 0:
        fnType, fnType_len = read_fn_type(f)
        payload_len -= fnType_len
        types.append(fnType)
    assert payload_len == 0
    print(types)
    print("  + Parsing type section done")
    return types


def read_fn_type(f):
    total_len = 0
    form, l = readVarUint(f, 7)
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
    return (form, param_count, param_types, return_count, return_types), total_len


def parse_value_type(f):
    ptype, l = readVarUint(f, 7)
    param_type = value_type(ptype)
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
    assert res == 0x0b
    return op, l + 1


def parse_opcode(f):
    byte = readUInt(f, 1)
    op = Opcode(byte)
    if op == Opcode.end:
        return endOpcode, 1
    elif op == Opcode.get_global:
        payload,l = readVarUint(f, 32)
        return (op, payload), 1 + l
    elif op == Opcode.i32_const:
        payload, l = readVarInt(f, 32)
        return (op, payload), 1 + l
    elif op == Opcode.i64_const:
        payload, l = readVarInt(f, 64)
        return (op, payload), 1 + l
    elif op == Opcode.f32_const:
        payload = readUInt(f, 4)
        return (op, payload), 5
    elif op == Opcode.f64_const:
        payload = readUInt(f, 8)
        return (op, payload), 9
    else:
        raise Exception("Todo implement")


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
    f.read(payload_len)
    print("  + Parsing code section done")


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
        print("Data entry [len = {:d}] = '{}...'".format(size, data[:16]))
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


def main():
    filename = sys.argv[1]
    with open(filename, "rb") as f:
        parse(f)


main()

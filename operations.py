from parser import Type
import math
import struct
import enum


def typeToStruct(type, signed):
    if signed:
        return {Type.i32: ('i', 31), Type.i64: ('q', 63), Type.f32: ('f', -1), Type.f64: ('d', -1)}[type]
    return {Type.i32: ('I', 32), Type.i64: ('Q', 64), Type.f32: ('f', -1), Type.f64: ('d', -1)}[type]

class StackValue:
    def __init__(self, type, val=None, signed=True):
        assert type in (Type.i32, Type.i64, Type.f32, Type.f64)
        self.type = type
        if val is not None:
            self.store(val, signed)
        else:
            if type in (Type.i32, Type.i64):
                self.store(0)
            else:
                self.store(0.0)


    def load(self, signed=True):
        struct_type, _ = typeToStruct(self.type, signed)
        return struct.unpack(struct_type, self.val)[0]

    def store(self, val, signed=True):
        struct_type, bits = typeToStruct(self.type, signed)
        if bits != -1:
            if val >= 0:
                val = val & ((2 ** bits) - 1) # truncate
            else:
                val = ~(~val & ((2 ** bits) - 1)) # truncate
        self.val = struct.pack(struct_type, val)

    def __repr__(self):
        return f"{self.type.name}({self.load()})"

# unary
def eqz(v, sgn): return StackValue(Type.i32, int(v.load(sgn) == 0))
def abs_(v, sgn): return StackValue(v.type, abs(v.load(sgn)))
def neg(v, sgn): return StackValue(v.type, -v.load(sgn))
def ceil_(v, sgn): return StackValue(v.type, math.ceil(v.load(sgn)))
def floor_(v, sgn): return StackValue(v.type, math.floor(v.load(sgn)))
def trunc_(v, sgn): return StackValue(v.type, math.trunc(v.load(sgn)))
def sqrt_(v, sgn): return StackValue(v.type, math.sqrt(v.load(sgn)))

# binary
def add(v1, v2, sgn): return StackValue(v1.type, v1.load(sgn) + v2.load(sgn), sgn)
def sub(v1, v2, sgn): return StackValue(v1.type, v1.load(sgn) - v2.load(sgn), sgn)
def mul(v1, v2, sgn): return StackValue(v1.type, v1.load(sgn) * v2.load(sgn), sgn)
def div_i(v1, v2, sgn): return StackValue(v1.type, v1.load(sgn) // v2.load(sgn), sgn)
def div_f(v1, v2, sgn): return StackValue(v1.type, v1.load(sgn) / v2.load(sgn), sgn)
def rem(v1, v2, sgn): return StackValue(v1.type, v1.load(sgn) % v2.load(sgn), sgn)

def and_(v1, v2, sgn): return StackValue(v1.type, v1.load(sgn) & v2.load(sgn), sgn)
def or_(v1, v2, sgn): return StackValue(v1.type, v1.load(sgn) | v2.load(sgn), sgn)
def xor(v1, v2, sgn): return StackValue(v1.type, v1.load(sgn) ^ v2.load(sgn), sgn)
def shl(v1, v2, sgn): return StackValue(v1.type, v1.load(sgn) << v2.load(sgn), sgn)
def shr_s(v1, v2, sgn): return StackValue(v1.type, v1.load(sgn) >> v2.load(sgn), sgn)
def _shr_u_impl(v1, v2, bits, sgn):
    val1 = v1.load(False); val2 = v2.load(False)
    return StackValue(v1.type, val1>>val2 if val1 >= 0 else (val1+(2**bits))>>val2, sgn)
def shr_u_32(v1, v2, sgn): return _shr_u_impl(v1, v2, 32, sgn)
def shr_u_64(v1, v2, sgn): return _shr_u_impl(v1, v2, 64, sgn)

def wrap32(v, sgn): return StackValue(Type.i32, v.load(sgn) & 0xffffffff, sgn)

def min_(v1, v2, sgn): return StackValue(Type.i32, min(v1.load(sgn), v2.load(sgn)), sgn)
def max_(v1, v2, sgn): return StackValue(Type.i32, max(v1.load(sgn), v2.load(sgn)), sgn)

def lt(v1, v2, sgn): return StackValue(Type.i32, int(v1.load(sgn) < v2.load(sgn)))
def gt(v1, v2, sgn): return StackValue(Type.i32, int(v1.load(sgn) > v2.load(sgn)))
def le(v1, v2, sgn): return StackValue(Type.i32, int(v1.load(sgn) <= v2.load(sgn)))
def ge(v1, v2, sgn): return StackValue(Type.i32, int(v1.load(sgn) >= v2.load(sgn)))
def eq(v1, v2, sgn): return StackValue(Type.i32, int(v1.load(sgn) == v2.load(sgn)))
def ne(v1, v2, sgn): return StackValue(Type.i32, int(v1.load(sgn) != v2.load(sgn)))

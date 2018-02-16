from parser import Type
import math


class StackValue:
    def __init__(self, type, val=None):
        assert type in (Type.i32, Type.i64, Type.f32, Type.f64)
        self.type = type
        if val is not None:
            self.val = val
        else:
            if type in (Type.i32, Type.i64):
                self.val = 0
            else:
                self.val = 0.0


    def __repr__(self):
        return f"{self.type.name}({self.val})"

# unary
def eqz(v): return StackValue(Type.i32, int(v.val == 0))
def abs_(v): return StackValue(v.type, abs(v.val))
def neg(v): return StackValue(v.type, -v.val)
def ceil_(v): return StackValue(v.type, math.ceil(v.val))
def floor_(v): return StackValue(v.type, math.floor(v.val))
def trunc_(v): return StackValue(v.type, math.trunc(v.val))
def sqrt_(v): return StackValue(v.type, math.sqrt(v.val))

# binary
def add(v1, v2): return StackValue(v1.type, v1.val + v2.val)
def sub(v1, v2): return StackValue(v1.type, v1.val - v2.val)
def mul(v1, v2): return StackValue(v1.type, v1.val * v2.val)
def div_i(v1, v2): return StackValue(v1.type, v1.val // v2.val)
def div_f(v1, v2): return StackValue(v1.type, v1.val / v2.val)
def rem(v1, v2): return StackValue(v1.type, v1.val % v2.val)

def and_(v1, v2): return StackValue(v1.type, v1.val & v2.val)
def or_(v1, v2): return StackValue(v1.type, v1.val | v2.val)
def xor(v1, v2): return StackValue(v1.type, v1.val ^ v2.val)
def shl(v1, v2): return StackValue(v1.type, v1.val << v2.val)
def shr(v1, v2): return StackValue(v1.type, v1.val >> v2.val)

def min_(v1, v2): return StackValue(Type.i32, min(v1.val, v2.val))
def max_(v1, v2): return StackValue(Type.i32, max(v1.val, v2.val))

def lt(v1, v2): return StackValue(Type.i32, int(v1.val < v2.val))
def gt(v1, v2): return StackValue(Type.i32, int(v1.val > v2.val))
def le(v1, v2): return StackValue(Type.i32, int(v1.val <= v2.val))
def ge(v1, v2): return StackValue(Type.i32, int(v1.val >= v2.val))
def eq(v1, v2): return StackValue(Type.i32, int(v1.val == v2.val))
def ne(v1, v2): return StackValue(Type.i32, int(v1.val != v2.val))

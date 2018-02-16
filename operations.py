from parser import Type


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

def lt(v1, v2): return StackValue(v1.type, v1.val < v2.val)
def gt(v1, v2): return StackValue(v1.type, v1.val > v2.val)
def le(v1, v2): return StackValue(v1.type, v1.val <= v2.val)
def ge(v1, v2): return StackValue(v1.type, v1.val >= v2.val)
def eq(v1, v2): return StackValue(v1.type, v1.val == v2.val)
def ne(v1, v2): return StackValue(v1.type, v1.val != v2.val)

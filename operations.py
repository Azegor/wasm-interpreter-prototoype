from parser import Type


class StackValue:
    def __init__(self, type, val=None):
        assert type in (Type.i32, Type.i64, Type.f32, Type.i64)
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

def add(v1, v2):
    assert v1.type == v2.type
    return StackValue(v1.type, v1.val + v2.val)

def xor(v1, v2):
    assert v1.type == v2.type
    return StackValue(v1.type, v1.val ^ v2.val)

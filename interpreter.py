import opcode
import parser
from sexpr import *
from opcode import Opcode as O

class Interpreter:
    def __init__(self, parse_res):
        self.parse_res = parse_res
        self.functions = []
        self.stack = self.Stack()
        self.ST = None # current stack top
        self.opFns = dict()
        self.init_op_fns()

    def initialize(self):
        data = self.parse_res
        assert len(data.function_section) == len(data.code_section)
        fns = data.function_section
        types = data.type_section
        bodies = data.code_section
        for id in range(len(data.function_section)):
            fn_type_idx = fns[id]
            fn_type = types[fn_type_idx]
            assert fn_type[0] == parser.Type.func or fn_type[0] == parser.Type.anyfunc
            fn_body = bodies[id]
            fn = self.Function(id, fn_type, fn_body)
            self.functions.append(fn)
            print(fn)

    def run_function(self, id, params):
        fn = self.functions[id]
        assert fn is not None
        assert len(params) == len(fn.type[1][0])
        print(" ### Executing function", SExprToStr(fn.type), "with parameters", params)
        frame = self.stack.push(len(params))
        self.ST = frame
        frame.setupCall(params, fn.locals)
        print(f"Current stack: {repr(self.stack)}")

        for instr in fn.code:
            self.execute_instr(instr)
            print(f"Current stack: {repr(self.stack)}")


        self.stack.pop()
        self.ST = self.stack.top()
        print(" +++ Done executing function", SExprToStr(fn.type))

    def execute_instr(self, instr):
        opFn = self.opFns[instr.opcode]
        assert opFn is not None
        print("executing", instr)
        opFn(instr.payload)

    class Function:
        def __init__(self, id, type, body):
            self.id = id
            self.type = type
            self.locals = body[0]
            self.code = body[1]

        def __repr__(self):
            return f"<FN type:{self.type} body: {self.body}>"

        def __str__(self):
            return SExprToStr(SExpr(self.type[0], (self.id,) + self.type[1:] + (self.locals, self.code)))

    class Stack:
        def __init__(self):
            self.frames = []

        def push(self, local_cnt):
            frame = Interpreter.StackFrame(local_cnt)
            self.frames.append(frame)
            return frame

        def pop(self):
            self.frames.pop()

        def top(self):
            if len(self.frames) > 0:
                return self.frames[-1]
            return None

        def __repr__(self):
            res = ""
            for f in self.frames:
                res += repr(f) + "\n"
            return res

    class StackFrame:
        def __init__(self, local_cnt):
            self.locals = []
            self.stack = []

        def setupCall(self, params, locals):
            for i in range(len(params)):
                self.locals.append(params[i])
            for l in locals:
                count = l[0]
                type = l[1]
                for i in range(count):
                    self.locals.append(Interpreter.StackValue(type))

        def load(self, localNr):
            local = self.locals[localNr]
            self.stack.append(local)

        def store(self, localNr):
            val = self.stack.pop()
            self.locals[localNr] = val

        def push(self, val):
            self.stack.append(val)

        def pop(self, val):
            return self.stack.pop()

        def __repr__(self):
            return f"Locals: {self.locals}, Stack: {self.stack}"

    class StackValue:
        def __init__(self, type, val=None):
            assert type in (parser.Type.i32, parser.Type.i64, parser.Type.f32, parser.Type.i64)
            self.type = type
            if val is not None:
                self.val = val
            else:
                if type in (parser.Type.i32, parser.Type.i64):
                    self.val = 0
                else:
                    self.val = 0.0


        def __repr__(self):
            return f"{self.type.name}({self.val})"

    # TODO: define operations

    def opTODO(self, payload):
        print("TODO: implement")
        assert False

    def init_op_fns(self):
        self.opFns = {
            O.unreachable: self.opTODO,
            O.nop: self.opTODO,
            O.block: self.opTODO,
            O.loop: self.opTODO,
            O.if_: self.opTODO,
            O.else_: self.opTODO,
            O.end: self.opTODO,
            O.br: self.opTODO,
            O.br_if: self.opTODO,
            O.br_table: self.opTODO,
            O.return_: self.opTODO,

            # call operators
            O.call: self.opTODO,
            O.call_indirect: self.opTODO,

            # parametric operators
            O.drop: self.opTODO,
            O.select: self.opTODO,

            # variable access
            O.get_local: lambda p: self.ST.load(p),
            O.set_local: self.opTODO,
            O.tee_local: self.opTODO,
            O.get_global: self.opTODO,
            O.set_global: self.opTODO,

            # memory related operators
            O.i32_load: self.opTODO,
            O.i64_load: self.opTODO,
            O.f32_load: self.opTODO,
            O.f64_load: self.opTODO,
            O.i32_load8_s: self.opTODO,
            O.i32_load8_u: self.opTODO,
            O.i32_load16_s: self.opTODO,
            O.i32_load16_u: self.opTODO,
            O.i64_load8_s: self.opTODO,
            O.i64_load8_u: self.opTODO,
            O.i64_load16_s: self.opTODO,
            O.i64_load16_u: self.opTODO,
            O.i64_load32_s: self.opTODO,
            O.i64_load32_u: self.opTODO,
            O.i32_store: self.opTODO,
            O.i64_store: self.opTODO,
            O.f32_store: self.opTODO,
            O.f64_store: self.opTODO,
            O.i32_store8: self.opTODO,
            O.i32_store16: self.opTODO,
            O.i64_store8: self.opTODO,
            O.i64_store16: self.opTODO,
            O.i64_store32: self.opTODO,
            O.current_memory: self.opTODO,
            O.grow_memory: self.opTODO,

            # Constants
            O.i32_const: self.opTODO,
            O.i64_const: self.opTODO,
            O.f32_const: self.opTODO,
            O.f64_const: self.opTODO,

            # comparison operators
            O.i32_eqz: self.opTODO,
            O.i32_eq: self.opTODO,
            O.i32_ne: self.opTODO,
            O.i32_lt_s: self.opTODO,
            O.i32_lt_u: self.opTODO,
            O.i32_gt_s: self.opTODO,
            O.i32_gt_u: self.opTODO,
            O.i32_le_s: self.opTODO,
            O.i32_le_u: self.opTODO,
            O.i32_ge_s: self.opTODO,
            O.i32_ge_u: self.opTODO,
            O.i64_eqz: self.opTODO,
            O.i64_eq: self.opTODO,
            O.i64_ne: self.opTODO,
            O.i64_lt_s: self.opTODO,
            O.i64_lt_u: self.opTODO,
            O.i64_gt_s: self.opTODO,
            O.i64_gt_u: self.opTODO,
            O.i64_le_s: self.opTODO,
            O.i64_le_u: self.opTODO,
            O.i64_ge_s: self.opTODO,
            O.i64_ge_u: self.opTODO,
            O.f32_eq: self.opTODO,
            O.f32_ne: self.opTODO,
            O.f32_lt: self.opTODO,
            O.f32_gt: self.opTODO,
            O.f32_le: self.opTODO,
            O.f32_ge: self.opTODO,
            O.f64_eq: self.opTODO,
            O.f64_ne: self.opTODO,
            O.f64_lt: self.opTODO,
            O.f64_gt: self.opTODO,
            O.f64_le: self.opTODO,
            O.f64_ge: self.opTODO,

            # numeric operators
            O.i32_clz: self.opTODO,
            O.i32_ctz: self.opTODO,
            O.i32_popcnt: self.opTODO,
            O.i32_add: self.opTODO,
            O.i32_sub: self.opTODO,
            O.i32_mul: self.opTODO,
            O.i32_div_s: self.opTODO,
            O.i32_div_u: self.opTODO,
            O.i32_rem_s: self.opTODO,
            O.i32_rem_u: self.opTODO,
            O.i32_and: self.opTODO,
            O.i32_or: self.opTODO,
            O.i32_xor: self.opTODO,
            O.i32_shl: self.opTODO,
            O.i32_shr_s: self.opTODO,
            O.i32_shr_u: self.opTODO,
            O.i32_rotl: self.opTODO,
            O.i32_rotr: self.opTODO,
            O.i64_clz: self.opTODO,
            O.i64_ctz: self.opTODO,
            O.i64_popcnt: self.opTODO,
            O.i64_add: self.opTODO,
            O.i64_sub: self.opTODO,
            O.i64_mul: self.opTODO,
            O.i64_div_s: self.opTODO,
            O.i64_div_u: self.opTODO,
            O.i64_rem_s: self.opTODO,
            O.i64_rem_u: self.opTODO,
            O.i64_and: self.opTODO,
            O.i64_or: self.opTODO,
            O.i64_xor: self.opTODO,
            O.i64_shl: self.opTODO,
            O.i64_shr_s: self.opTODO,
            O.i64_shr_u: self.opTODO,
            O.i64_rotl: self.opTODO,
            O.i64_rotr: self.opTODO,
            O.f32_abs: self.opTODO,
            O.f32_neg: self.opTODO,
            O.f32_ceil: self.opTODO,
            O.f32_floor: self.opTODO,
            O.f32_trunc: self.opTODO,
            O.f32_nearest: self.opTODO,
            O.f32_sqrt: self.opTODO,
            O.f32_add: self.opTODO,
            O.f32_sub: self.opTODO,
            O.f32_mul: self.opTODO,
            O.f32_div: self.opTODO,
            O.f32_min: self.opTODO,
            O.f32_max: self.opTODO,
            O.f32_copysign: self.opTODO,
            O.f64_abs: self.opTODO,
            O.f64_neg: self.opTODO,
            O.f64_ceil: self.opTODO,
            O.f64_floor: self.opTODO,
            O.f64_trunc: self.opTODO,
            O.f64_nearest: self.opTODO,
            O.f64_sqrt: self.opTODO,
            O.f64_add: self.opTODO,
            O.f64_sub: self.opTODO,
            O.f64_mul: self.opTODO,
            O.f64_div: self.opTODO,
            O.f64_min: self.opTODO,
            O.f64_max: self.opTODO,
            O.f64_copysign: self.opTODO,

            # conversions
            O.i32_wrap_i64: self.opTODO,
            O.i32_trunc_s_f32: self.opTODO,
            O.i32_trunc_u_f32: self.opTODO,
            O.i32_trunc_s_f64: self.opTODO,
            O.i32_trunc_u_f64: self.opTODO,
            O.i64_extend_s_i32: self.opTODO,
            O.i64_extend_u_i32: self.opTODO,
            O.i64_trunc_s_f32: self.opTODO,
            O.i64_trunc_u_f32: self.opTODO,
            O.i64_trunc_s_f64: self.opTODO,
            O.i64_trunc_u_f64: self.opTODO,
            O.f32_convert_s_i32: self.opTODO,
            O.f32_convert_u_i32: self.opTODO,
            O.f32_convert_s_i64: self.opTODO,
            O.f32_convert_u_i64: self.opTODO,
            O.f32_demote_f64: self.opTODO,
            O.f64_convert_s_i32: self.opTODO,
            O.f64_convert_u_i32: self.opTODO,
            O.f64_convert_s_i64: self.opTODO,
            O.f64_convert_u_i64: self.opTODO,
            O.f64_promote_f32: self.opTODO,

            # reinterpretations
            O.i32_reinterpret_f32: self.opTODO,
            O.i64_reinterpret_f64: self.opTODO,
            O.f32_reinterpret_i32: self.opTODO,
            O.f64_reinterpret_i64: self.opTODO,
        }

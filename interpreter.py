import opcode
import parser
from sexpr import *
from opcode import Opcode as O
from operations import *


class Interpreter:
    def __init__(self, parse_res):
        self.parse_res = parse_res
        self.functions = []
        self.stack = self.Stack()
        self.instr_ptr = 0
        self.InstrPtrStack = []
        self.ST = None # current stack top
        self.opFns = dict()
        self.init_op_fns()
        self.jump_offset = 0
        self.exp_fn = {}

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
            locals, fn_code = bodies[id]
            body = self.InstrBlock()
            body.createInnerBlocks(fn_code)
            fn = self.Function(id, fn_type, locals, body, fn_code)
            self.functions.append(fn)

        for name, type, id in data.export_section:
            if type is parser.ExternalKind.Func:
                self.exp_fn[name] = id



    def run_function(self, id, params):
        fn = self.functions[id]
        assert fn is not None
        assert len(params) == len(fn.params_types())
        print(" ### Executing function", SExprToStr(fn.type), "with parameters", params)
        frame = self.stack.push(len(params))
        self.ST = frame
        frame.setupCall(params, fn.locals)
        print(f"Current stack: {repr(self.stack)}")

        codelen = len(fn.code)
        while self.instr_ptr < codelen:
            print(f"@{self.instr_ptr}")
            self.execute_instr(fn.code[self.instr_ptr])
            print(f"Current stack: {repr(self.stack)}")
            self.instr_ptr += 1

        # handle return
        returntype = fn.type[1][1]
        if len(returntype) > 0:
            assert self.ST.size() == 1
            type = returntype[0]
            return_val = self.ST.pop()
            assert type == return_val.type
        else:
            assert self.ST.size() == 0
            return_val = None


        self.stack.pop()
        self.ST = self.stack.top()
        print(" +++ Done executing function", SExprToStr(fn.type))

        print("returning", return_val)
        return return_val

    def run_exported_fn(self, name, args):
        fnId = self.exp_fn.get(name)
        if fnId is None:
            raise Exception(f"Unknown function {name}")
        params = []
        param_types = self.functions[fnId].params_types()
        assert len(param_types) == len(args)
        for i in range(len(args)):
            a = args[i]
            type = param_types[i]
            if type in (Type.i32, Type.i64):
                params.append(StackValue(type, int(a)))
            else:
                params.append(StackValue(type, float(a)))
        self.run_function(fnId, params)

    def execute_instr(self, instr):
        opFn = self.opFns[instr.opcode]
        assert opFn is not None
        print("executing", instr)
        opFn(instr.payload)

    class InstrBlock:
        def __init__(self, type = None, parent = None):
            self.type = type
            self.startOffs = -1
            self.elseOffs = -1 # optional
            self.endOffs = -1
            self.parent = parent
            self.depth = -1

        def createInnerBlocks(self, instrList, startOffset = 0, depth = 0):
            self.depth = depth
            self.startOffs = startOffset
            i = startOffset + 1
            end = len(instrList)
            is_if = instrList[startOffset].opcode == O.if_
            while i < end:
                op = instrList[i]
                if op.opcode in (O.if_, O.loop, O.block): # nested even more
                    blk = Interpreter.InstrBlock(op.payload, self)
                    instrList[i] = opcode.Op(op.opcode, blk) # replace instr.
                    i = blk.createInnerBlocks(instrList, i, depth + 1) # skip over the instrs.
                elif op.opcode == O.end:
                    self.endOffs = i
                    return i
                elif is_if and op.opcode == O.else_:
                    assert self.elseOffs == -1 # can only be there once
                    instrList[i] = opcode.Op(op.opcode, self) # replace instr.
                    self.elseOffs = i
                i += 1
            return i

        def __repr__(self):
            return f"[Block depth={self.depth}, len={self.endOffs - self.startOffs}]"

    class Function:
        def __init__(self, id, type, locals, body, code):
            self.id = id
            self.type = type
            self.locals = locals
            self.body = body # necessary?
            self.code = code

        def __repr__(self):
            return f"<FN type:{self.type} body: {self.body}>"

        def __str__(self):
            return SExprToStr(SExpr(self.type[0], (self.id,) + self.type[1:] + (self.locals, self.code)))

        def params_types(self):
            return self.type[1][0]

        def return_types(self):
            return self.type[1][1]

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
                    self.locals.append(StackValue(type))

        def load(self, localNr):
            local = self.locals[localNr]
            self.stack.append(local)

        def store(self, localNr):
            val = self.stack.pop()
            self.locals[localNr] = val

        def push(self, val):
            self.stack.append(val)

        def push_new(self, type, val):
            self.stack.append(StackValue(type, val))

        def pop(self):
            return self.stack.pop()

        def size(self):
            return len(self.stack)

        def __repr__(self):
            return f"Locals: {self.locals}, Stack: {self.stack}"

    # TODO: define operations

    def opTODO(self, payload):
        raise Exception("TODO implement")

    def unaryOp(self, calledFn):
        val = self.ST.pop()
        res = calledFn(val)
        self.ST.push(res)

    def binOp(self, calledFn):
        val2 = self.ST.pop()
        val1 = self.ST.pop()
        assert val1.type == val2.type
        res = calledFn(val1, val2)
        self.ST.push(res)

    def opIf(self, payload):
        do_branch = self.ST.pop()
        assert do_branch.type == Type.i32
        if do_branch.val == 0:
            self.instr_ptr = payload.elseOffs

    def opElse(self, payload):
        self.instr_ptr = payload.endOffs

    def opCall(self, fnid):
        fn = self.functions[fnid]
        param_types = fn.params_types()
        args = []
        for pt in param_types: # TODO is this the right order or backwards?
            print (pt)
            p = self.ST.pop()
            assert p.type == pt
            args.append(p)
        self.InstrPtrStack.append(self.instr_ptr)
        self.instr_ptr = 0
        return_val = self.run_function(fnid, tuple(args))
        self.instr_ptr = self.InstrPtrStack.pop()
        self.ST.push(return_val)

    def opNothing(self, payload):
        print("End of Block")
        pass


    def init_op_fns(self):
        S = self.ST
        # TODO distinguish between signed and unsigned values!
        self.opFns = {
            O.unreachable: self.opTODO,
            O.nop: self.opTODO,
            O.block: self.opTODO,
            O.loop: self.opTODO,
            O.if_: self.opIf,
            O.else_: self.opElse,
            O.end: self.opNothing,
            O.br: self.opTODO,
            O.br_if: self.opTODO,
            O.br_table: self.opTODO,
            O.return_: self.opTODO,

            # call operators
            O.call: self.opCall,
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
            O.i32_const: lambda p: self.ST.push_new(parser.Type.i32, p),
            O.i64_const: lambda p: self.ST.push_new(parser.Type.i64, p),
            O.f32_const: lambda p: self.ST.push_new(parser.Type.f32, p),
            O.f64_const: lambda p: self.ST.push_new(parser.Type.f64, p),

            # comparison operators
            O.i32_eqz: lambda p: self.unaryOp(eqz),
            O.i64_eq: lambda p: self.binOp(eq),
            O.i64_ne: lambda p: self.binOp(ne),
            O.i32_lt_s: lambda p: self.binOp(lt),
            O.i32_lt_u: lambda p: self.binOp(lt),
            O.i32_gt_s: lambda p: self.binOp(gt),
            O.i32_gt_u: lambda p: self.binOp(gt),
            O.i32_le_s: lambda p: self.binOp(le),
            O.i32_le_u: lambda p: self.binOp(le),
            O.i32_ge_s: lambda p: self.binOp(ge),
            O.i32_ge_u: lambda p: self.binOp(ge),
            O.i64_eqz: lambda p: self.unaryOp(eqz),
            O.i64_eq: lambda p: self.binOp(eq),
            O.i64_ne: lambda p: self.binOp(ne),
            O.i64_lt_s: lambda p: self.binOp(lt),
            O.i64_lt_u: lambda p: self.binOp(lt),
            O.i64_gt_s: lambda p: self.binOp(gt),
            O.i64_gt_u: lambda p: self.binOp(gt),
            O.i64_le_s: lambda p: self.binOp(le),
            O.i64_le_u: lambda p: self.binOp(le),
            O.i64_ge_s: lambda p: self.binOp(ge),
            O.i64_ge_u: lambda p: self.binOp(ge),
            O.f32_eq: lambda p: self.binOp(eq),
            O.f32_ne: lambda p: self.binOp(ne),
            O.f32_lt: lambda p: self.binOp(lt),
            O.f32_gt: lambda p: self.binOp(gt),
            O.f32_le: lambda p: self.binOp(le),
            O.f32_ge: lambda p: self.binOp(ge),
            O.f64_eq: lambda p: self.binOp(eq),
            O.f64_ne: lambda p: self.binOp(ne),
            O.f64_lt: lambda p: self.binOp(lt),
            O.f64_gt: lambda p: self.binOp(gt),
            O.f64_le: lambda p: self.binOp(le),
            O.f64_ge: lambda p: self.binOp(ge),

            # numeric operators
            O.i32_clz: self.opTODO,
            O.i32_ctz: self.opTODO,
            O.i32_popcnt: self.opTODO,
            O.i32_add: lambda p: self.binOp(add),
            O.i32_sub: lambda p: self.binOp(sub),
            O.i32_mul: lambda p: self.binOp(mul),
            O.i32_div_s: lambda p: self.binOp(div_i),
            O.i32_div_u: lambda p: self.binOp(div_i),
            O.i32_rem_s: lambda p: self.binOp(rem),
            O.i32_rem_u: lambda p: self.binOp(rem),
            O.i32_and: lambda p: self.binOp(and_),
            O.i32_or: lambda p: self.binOp(or_),
            O.i32_xor: lambda p: self.binOp(xor),
            O.i32_shl: lambda p: self.binOp(shl),
            O.i32_shr_s: lambda p: self.binOp(shr),
            O.i32_shr_u: self.opTODO,
            O.i32_rotl: self.opTODO,
            O.i32_rotr: self.opTODO,
            O.i64_clz: self.opTODO,
            O.i64_ctz: self.opTODO,
            O.i64_popcnt: self.opTODO,
            O.i64_add: lambda p: self.binOp(add),
            O.i64_sub: lambda p: self.binOp(sub),
            O.i64_mul: lambda p: self.binOp(mul),
            O.i64_div_s: lambda p: self.binOp(div_i),
            O.i64_div_u: lambda p: self.binOp(div_i),
            O.i64_rem_s: lambda p: self.binOp(rem),
            O.i64_rem_u: lambda p: self.binOp(rem),
            O.i64_and: lambda p: self.binOp(and_),
            O.i64_or: lambda p: self.binOp(or_),
            O.i64_xor: lambda p: self.binOp(xor),
            O.i64_shl: lambda p: self.binOp(shl),
            O.i64_shr_s: lambda p: self.binOp(shr),
            O.i64_shr_u: self.opTODO,
            O.i64_rotl: self.opTODO,
            O.i64_rotr: self.opTODO,
            O.f32_abs: lambda p: self.unaryOp(abs_),
            O.f32_neg: lambda p: self.unaryOp(neg),
            O.f32_ceil: lambda p: self.unaryOp(ceil_),
            O.f32_floor: lambda p: self.unaryOp(floor_),
            O.f32_trunc: lambda p: self.unaryOp(trunc_),
            O.f32_nearest: self.opTODO,
            O.f32_sqrt: lambda p: self.unaryOp(sqrt_),
            O.f32_add: lambda p: self.binOp(add),
            O.f32_sub: lambda p: self.binOp(sub),
            O.f32_mul: lambda p: self.binOp(mul),
            O.f32_div: lambda p: self.binOp(div_f),
            O.f32_min: lambda p: self.binOp(min_),
            O.f32_max: lambda p: self.binOp(max_),
            O.f32_copysign: self.opTODO,
            O.f64_abs: lambda p: self.unaryOp(abs_),
            O.f64_neg: lambda p: self.unaryOp(neg),
            O.f64_ceil: lambda p: self.unaryOp(ceil_),
            O.f64_floor: lambda p: self.unaryOp(floor_),
            O.f64_trunc: lambda p: self.unaryOp(trunc_),
            O.f64_nearest: self.opTODO,
            O.f64_sqrt: lambda p: self.unaryOp(sqrt_),
            O.f64_add: lambda p: self.binOp(add),
            O.f64_sub: lambda p: self.binOp(sub),
            O.f64_mul: lambda p: self.binOp(mul),
            O.f64_div: lambda p: self.binOp(div_f),
            O.f64_min: lambda p: self.binOp(min_),
            O.f64_max: lambda p: self.binOp(max_),
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

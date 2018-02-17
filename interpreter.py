import opcode
import parser
from opcode import Opcode as O
from operations import *


class Interpreter:
    def __init__(self, parse_res):
        self.parse_res = parse_res
        self.functions = []
        self.stack = self.Stack()
        self.instr_ptr = 0
        self.InstrPtrStack = []
        self.BlockStackSizes = []
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
        print(" ### Executing function", fn.type, "with parameters", params)
        frame = self.stack.push(len(params))
        self.ST = frame
        frame.setupCall(params, fn.locals)
        print(f"Current stack: {repr(self.stack)}")

        codelen = len(fn.code)
        print(fn.code)
        while self.instr_ptr < codelen:
            print(f"\n@{self.instr_ptr}")
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
        print(" +++ Done executing function", fn.type)

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
        result = self.run_function(fnId, params)
        print(f"#### Result = {result.load()} ####")

    def execute_instr(self, instr):
        opFn = self.opFns[instr.opcode]
        assert opFn is not None
        print("executing", instr)
        opFn(instr.payload)

    class InstrBlock:
        def __init__(self, type = None, parent = None):
            self.type = type
            self.kind = O.unreachable
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
            self.kind = instrList[startOffset].opcode
            while i < end:
                op = instrList[i]
                if op.opcode in (O.if_, O.loop, O.block): # nested even more
                    blk = Interpreter.InstrBlock(op.payload, self)
                    instrList[i] = opcode.Op(op.opcode, blk) # replace instr.
                    i = blk.createInnerBlocks(instrList, i, depth + 1) # skip over the instrs.
                elif op.opcode == O.end:
                    self.endOffs = i
                    instrList[i] = opcode.Op(op.opcode, self)
                    return i
                elif self.kind == O.if_ and op.opcode == O.else_:
                    assert self.elseOffs == -1 # can only be there once
                    instrList[i] = opcode.Op(op.opcode, self) # replace instr.
                    self.elseOffs = i
                elif op.opcode in (O.br, O.br_if):
                    break_depth = op.payload
                    break_blk = self
                    for i in range(break_depth):
                        break_blk = break_depth.parent
                        assert break_blk is not None
                    instrList[i] = opcode.Op(op.opcode, break_blk)
                elif op.opcode == O.return_:
                    instrList[i] = opcode.Op(op.opcode, len(instrList) - 1)
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
            return f"Size: {len(self.frames)}; Top Entry -> {self.frames[-1]}"

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

        def tee(self, localNr):
            val = self.stack[-1]
            self.locals[localNr] = val

        def push(self, val):
            self.stack.append(val)

        def push_new(self, type, val):
            self.stack.append(StackValue(type, val))

        def pop(self):
            return self.stack.pop()

        def size(self):
            return len(self.stack)

        def pop_upto(self, size):
            if size > self.size():
                print("#### pruning OpStack ####")
                self.stack = self.stack[:size]

        def __repr__(self):
            return f"Locals: {self.locals}, OpStack: {self.stack}"

    # TODO: define operations

    def opTODO(self, payload):
        raise Exception("TODO implement")

    def unaryOp(self, calledFn, signed=True):
        val = self.ST.pop()
        res = calledFn(val, signed)
        self.ST.push(res)

    def binOp(self, calledFn, signed=True):
        val2 = self.ST.pop()
        val1 = self.ST.pop()
        assert val1.type == val2.type
        res = calledFn(val1, val2, signed)
        self.ST.push(res)
        print (f"{val1} {calledFn.__name__} {val2} = {res}")

    def binOpDiffType(self, calledFn, signed=True):
        val2 = self.ST.pop()
        val1 = self.ST.pop()
        res = calledFn(val1, val2, signed)
        self.ST.push(res)
        print (f"{val1} {calledFn.__name__} {val2} = {res}")

    def opIf(self, block):
        do_branch = self.ST.pop()
        assert do_branch.type == Type.i32
        if do_branch.load() == 0:
            self.instr_ptr = block.elseOffs

    def opElse(self, block):
        self.instr_ptr = block.endOffs
        self.adjust_opstack()

    def opCall(self, fnid):
        fn = self.functions[fnid]
        param_types = fn.params_types()
        args = []
        for pt in param_types:
            p = self.ST.pop()
            assert p.type == pt
            args.append(p)
        self.InstrPtrStack.append(self.instr_ptr)
        self.instr_ptr = 0
        return_val = self.run_function(fnid, tuple(args.reverse()))  # TODO is this the right order or backwards?
        self.instr_ptr = self.InstrPtrStack.pop()
        self.ST.push(return_val)

    def opBr(self, block):
        self.instr_ptr = block.endOffs
        self.adjust_opstack()
        # TODO: unwind operand stack!

    def opBrIf(self, block):
        do_branch = self.ST.pop()
        assert do_branch.type == Type.i32
        if do_branch.load() != 0:
            self.opBr(block)

    def opEnd(self, block):
        print("Block kind:", block.kind, end=" ")
        if block.kind == O.loop:
            self.instr_ptr = block.startOffs
            print("-> looping")
        else:
            print("-> leaving the block -> pop operands")
            self.adjust_opstack()

    def opBlockStart(self, payload):
        self.save_opstack()

    def opReturn(self, target):
        print("Jump to the End")
        self.instr_ptr = target

    def opNothing(self, payload):
        print("Doing Nothing")
        pass

    def save_opstack(self):
        self.BlockStackSizes.append(self.ST.size())

    def adjust_opstack(self):
        self.ST.pop_upto(self.BlockStackSizes.pop())


    def init_op_fns(self):
        S = self.ST
        self.opFns = {
            O.unreachable: self.opTODO,
            O.nop: self.opTODO,
            O.block: self.opBlockStart,
            O.loop: self.opBlockStart,
            O.if_: self.opIf,
            O.else_: self.opElse,
            O.end: self.opEnd,
            O.br: self.opTODO,
            O.br_if: self.opBrIf,
            O.br_table: self.opTODO,
            O.return_: self.opReturn,

            # call operators
            O.call: self.opCall,
            O.call_indirect: self.opTODO,

            # parametric operators
            O.drop: self.opTODO,
            O.select: self.opTODO,

            # variable access
            O.get_local: lambda p: self.ST.load(p),
            O.set_local: lambda p: self.ST.store(p),
            O.tee_local: lambda p: self.ST.tee(p),
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
            O.i32_lt_u: lambda p: self.binOp(lt, False),
            O.i32_gt_s: lambda p: self.binOp(gt),
            O.i32_gt_u: lambda p: self.binOp(gt, False),
            O.i32_le_s: lambda p: self.binOp(le),
            O.i32_le_u: self.opTODO,
            O.i32_ge_s: lambda p: self.binOp(ge),
            O.i32_ge_u: self.opTODO,
            O.i64_eqz: lambda p: self.unaryOp(eqz),
            O.i64_eq: lambda p: self.binOp(eq),
            O.i64_ne: lambda p: self.binOp(ne),
            O.i64_lt_s: lambda p: self.binOp(lt),
            O.i64_lt_u: self.opTODO,
            O.i64_gt_s: lambda p: self.binOp(gt),
            O.i64_gt_u: self.opTODO,
            O.i64_le_s: lambda p: self.binOp(le),
            O.i64_le_u: self.opTODO,
            O.i64_ge_s: lambda p: self.binOp(ge),
            O.i64_ge_u: self.opTODO,
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
            O.i32_div_u: self.opTODO,
            O.i32_rem_s: lambda p: self.binOp(rem),
            O.i32_rem_u: self.opTODO,
            O.i32_and: lambda p: self.binOp(and_),
            O.i32_or: lambda p: self.binOp(or_),
            O.i32_xor: lambda p: self.binOp(xor),
            O.i32_shl: lambda p: self.binOpDiffType(shl),
            O.i32_shr_s: lambda p: self.binOpDiffType(shr_s),
            O.i32_shr_u: lambda p: self.binOpDiffType(shr_u_32),
            O.i32_rotl: self.opTODO,
            O.i32_rotr: self.opTODO,
            O.i64_clz: self.opTODO,
            O.i64_ctz: self.opTODO,
            O.i64_popcnt: self.opTODO,
            O.i64_add: lambda p: self.binOp(add),
            O.i64_sub: lambda p: self.binOp(sub),
            O.i64_mul: lambda p: self.binOp(mul),
            O.i64_div_s: lambda p: self.binOp(div_i),
            O.i64_div_u: self.opTODO,
            O.i64_rem_s: lambda p: self.binOp(rem),
            O.i64_rem_u: self.opTODO,
            O.i64_and: lambda p: self.binOp(and_),
            O.i64_or: lambda p: self.binOp(or_),
            O.i64_xor: lambda p: self.binOp(xor),
            O.i64_shl: lambda p: self.binOpDiffType(shl),
            O.i64_shr_s: lambda p: self.binOpDiffType(shr_s),
            O.i64_shr_u: lambda p: self.binOpDiffType(shr_u_64),
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
            O.i32_wrap_i64: lambda p: self.unaryOp(wrap32),
            O.i32_trunc_s_f32: self.opTODO,
            O.i32_trunc_u_f32: self.opTODO,
            O.i32_trunc_s_f64: self.opTODO,
            O.i32_trunc_u_f64: self.opTODO,
            O.i64_extend_s_i32: self.opNothing,
            O.i64_extend_u_i32: self.opNothing,
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

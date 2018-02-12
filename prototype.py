#!/usr/bin/python3
import sys

import parser


class Function:
    def __init__(self, type, body):
        self.type = type
        self.body = body

    def __repr__(self):
        return f"<FN type:{self.type} body: {self.body}>"


def createStructures(data):
    assert len(data.function_section) == len(data.code_section)
    fns = data.function_section
    types = data.type_section
    bodies = data.code_section
    functions = []
    for i in range(len(data.function_section)):
        fn_type_idx = fns[i]
        fn_type = types[fn_type_idx]
        assert fn_type[0] == parser.TypeConstructor.func or fn_type[0] == parser.TypeConstructor.anyfunc
        fn_body = bodies[i]
        fn = Function(fn_type, fn_body)
        functions.append(fn)
    for fn in functions:
        print(fn)


def runMainFn():
    pass


def main():
    filename = sys.argv[1]
    print(f"Parsing '{filename}'")
    with open(filename, "rb") as f:
        p = parser.Parser(f)
        res = p.parse()
    createStructures(res)
    if res.start_section is not None:
        runMainFn()

main()

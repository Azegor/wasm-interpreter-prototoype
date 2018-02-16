#!/usr/bin/python3
import sys

import parser
from interpreter import Interpreter
from operations import StackValue


def main():
    filename = sys.argv[1]
    print(f"Parsing '{filename}'")
    with open(filename, "rb") as f:
        p = parser.Parser(f)
        res = p.parse()
    interpr = Interpreter(res)
    interpr.initialize()
    if len(sys.argv) > 2:
        fn_name = sys.argv[2]
        args = sys.argv[3:]
        params = []
        for a in args:
            params.append(StackValue(parser.Type.i32, int(a))) # only i32 for now

        interpr.run_exported_fn(fn_name, tuple(params))


main()

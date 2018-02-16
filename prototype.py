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
        interpr.run_exported_fn(fn_name, args)


main()

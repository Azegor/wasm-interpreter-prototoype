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
    interpr.run_function(0, (StackValue(parser.Type.i32, 42),))


main()

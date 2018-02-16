def SExprToStr(sexpr):
    if type(sexpr) is SExpr:
        if len(sexpr.tail) == 0:
            if sexpr.print_empty:
                return str(sexpr.head)
            return ""
        return f'({str(sexpr.head)} ' + ' '.join([SExprToStr(e) for e in sexpr.tail]) + ')'
    if type(sexpr) in (list, tuple):
        if len(sexpr) == 0:
            return ''
        return '(' + ' '.join([SExprToStr(e) for e in sexpr]) + ')'
    return repr(sexpr)


def printSExprList(slist, indent=0):
    indentStr = " " * indent
    for e in slist:
        print(indentStr, SExprToStr(e), sep="")


class SExpr:
    def __init__(self, head, tail, print_empty = True):
        self.head = head
        if type(tail) in (list, tuple):
            self.tail = tail
        else:
            self.tail = (tail,)
        self.print_empty = print_empty

    def __str__(self):
        return SExprToStr(self)

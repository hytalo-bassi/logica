import inspect
import re
from enum import Enum
from rich.console import Console
from rich.table import Table


class Operations(Enum):
    AND = 0
    OR = 1


Operations = Enum('Operations', ['AND', 'OR'])


def get_operation(char: str):
    if char == '+':
        return Operations.OR

    return Operations.AND

class Logic:


    def value(self):
        return


    def to_expr(self):
        return


class Bits:
    bits = ''
    
    @property
    def size(self):
        print(self.bits)
        return len(self.bits)

    @staticmethod
    def get_bits(n: int = 1):
        return '0' * n


    def __init__(self, n: int = 1):
        self.bits = Bits.get_bits(n)
    

    def at(self, i: int = 0):
        if i < 0 or i > len(self.bits):
            i = 0
        return self.bits[i] == '1'

    
    def set(self, n: int):
        size = len(self.bits)
        self.bits = bin(n)[2:].zfill(size)


    def __add__(self, n: int):
        v = int(self.bits, base = 2) + n
        if v > 2**len(self.bits):
            v = 0
        
        self.set(v)


    def realloc(self, x: int = 1):
        size = len(self.bits)
        self.bits = Bits.get_bits(size + x)
        return size + x - 1


class Variable(Logic):
    i = None
    symbol = 'None'
    bits = None


    def __init__(self, bits: Bits, i = 0, symbol = 'None'):
        self.bits = bits
        self.i = i
        self.symbol = symbol


    def get(self):
        return self.bits.at(self.i)


    def value(self):
        return self.get()


    def to_expr(self):
        return self.symbol


class Node(Logic):
    left = None
    right = None
    op = None
    var = None
    

    def __init__(self, left = None, right = None, op: int = None):
        self.left = left
        self.right = right
        self.op = op
    

    def get(self):
        if self.op == Operations.AND:
            return self.left.get() and self.right.get()
        else:
            return self.left.get() or self.right.get()


    def to_expr(self):
        left_expr = self.left.to_expr()
        right_expr = self.right.to_expr()

        if isinstance(self.left, Node):
            left_expr = f"({left_expr})"
        if isinstance(self.right, Node):
            right_expr = f"({right_expr})"

        middle = " ∨ " if self.op == Operations.OR else " ∧ "

        return left_expr + middle + right_expr


def get_truth_row(varlist):
    row = []
    for var in varlist:
        row.append(str(var.get())[0])
    return row


def get_tokens(s: str):
    tokens = []
    i = 0
    for char in s:
        if char == '+':
            tokens.append({ 'i': i, 'score': 2 })
        elif char == '*':
            tokens.append({ 'i': i, 'score': 1 })
        i += 1
    return tokens


def left_and_right(s: str, i: int):
    return [s[:i], s[i + 1:]]


def least_precedence(tokens: dict):
    if len(tokens) == 0: return -1

    M = tokens[0]['score']
    i_max = 0
    i = 0

    while (i < len(tokens)):
        token = tokens[i]
        token_scr = token['score']
        
        if token_scr > M:
            i_max = i
        
        i += 1
    
    return i_max


def _parser(expr: str, symboldict: dict, bits):
    tokens = get_tokens(expr)
    current_token_i = least_precedence(tokens)
    
    if current_token_i < 0:
        # if variable is already known
        if expr in symboldict:
            return symboldict[expr]

        i = bits.realloc()

        v = Variable(bits, symbol = expr, i = i)
        symboldict[expr] = v
        
        return v

    op_i = tokens[current_token_i]['i']
    
    op = expr[op_i]
    left_expr, right_expr = left_and_right(expr, op_i)
    
    left_node = _parser(left_expr, symboldict, bits)
    right_node = _parser(right_expr, symboldict, bits)
    
    n = Node(left = left_node, right = right_node, op = get_operation(op))
    return n


def parser(expr: str):
    symboldict = {}
    bits = Bits(0)
    return [_parser(expr, symboldict, bits), symboldict, bits]


def main():
    s = input()
    n, s, bits = parser(s)
    table = []
    tab_rich = Table()
    i = 0
    table = []
    for var in s:
        tab_rich.add_column(var, justify = "center")
        table.append(s[var])
    
    tab_rich.add_column(n.to_expr(), justify = "center")
    for i in range(0, 2**len(s)):
        tab_rich.add_row(*get_truth_row(table), str(n.get())[0])
        bits + 1

    console = Console()
    console.print(tab_rich)


main()


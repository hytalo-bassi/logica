from enum import Enum
from rich.console import Console
from rich.table import Table


class Laws(Enum):
    DOMINANCE = 0


class Operations(Enum):
    NOT = 0
    AND = 1
    OR = 2
    IMPLIES = 3
    DUAL_IMPLICATION = 4


def get_operation(char: str):
    if char == "+":
        return Operations.OR

    return Operations.AND


class Logic:

    def value(self):
        return

    def to_expr(self):
        return


class Bits:
    bits = ""

    @property
    def size(self):
        print(self.bits)
        return len(self.bits)

    @staticmethod
    def get_bits(n: int = 1):
        return "0" * n

    def __init__(self, n: int = 1):
        self.bits = Bits.get_bits(n)

    def at(self, i: int = 0):
        if i < 0 or i > len(self.bits):
            i = 0
        return self.bits[i] == "1"

    def set(self, n: int):
        size = len(self.bits)
        self.bits = bin(n)[2:].zfill(size)

    def __add__(self, n: int):
        v = int(self.bits, base=2) + n
        if v > 2 ** len(self.bits):
            v = 0

        self.set(v)

    def realloc(self, x: int = 1):
        size = len(self.bits)
        self.bits = Bits.get_bits(size + x)
        return size + x - 1


class Variable(Logic):
    i = None
    symbol = "None"
    bits = None
    fixed_value = None

    def __init__(self, bits: Bits = None, i=0, symbol="None", fixed_value: bool = None):
        if fixed_value is not None:
            self.fixed_value = fixed_value
            self.symbol = "T" if fixed_value else "F"
            return
        self.bits = bits
        self.i = i
        self.symbol = symbol

    def get(self):
        if self.fixed_value is not None:
            return self.fixed_value
        return self.bits.at(self.i)

    def value(self):
        return self.get()

    def to_expr(self):
        return self.symbol


# Useful when you dont want to have multiple possible values
Truth = Variable(fixed_value=True)
Falsity = Variable(fixed_value=False)


class Node(Logic):
    left = None
    right = None
    op = None
    var = None

    def __init__(self, left=None, right=None, op: int = None):
        self.left = left
        self.right = right
        self.op = op

    def get(self):
        if self.op == Operations.AND:
            return self.left.get() and self.right.get()
        elif self.op == Operations.OR:
            return self.left.get() or self.right.get()
        elif self.op == Operations.IMPLIES:
            if self.left.get() and not self.right.get():
                return False
            return True
        elif self.op == Operations.DUAL_IMPLICATION:
            if self.left.get() is not self.right.get():
                return False
            return True
        elif self.op == Operations.NOT:
            return not self.right.get()

    def to_expr(self):
        left_expr = self.left.to_expr() if self.left is not None else None
        right_expr = self.right.to_expr()

        if isinstance(self.left, Node) and self.left.op != Operations.NOT:
            left_expr = f"({left_expr})"
        if isinstance(self.right, Node) and self.right.op != Operations.NOT:
            right_expr = f"({right_expr})"

        middle = ""
        if self.op == Operations.OR:
            middle = " ∨ "
        elif self.op == Operations.AND:
            middle = " ∧ "
        elif self.op == Operations.IMPLIES:
            middle = " → "
        elif self.op == Operations.DUAL_IMPLICATION:
            middle = " ≡ "
        elif self.op == Operations.NOT:
            # Operations.NOT is a special type of Node that only have the right side.
            # That's why the different approach in returning the expr.

            return "¬" + right_expr

        return left_expr + middle + right_expr


def get_truth_row(varlist):
    row = []
    for var in varlist:
        row.append(str(var.get())[0])
    return row


def tokenize(s: str):
    # ensures that the parser will be able to understand the correct order.
    open_parens = 0
    tokens = []
    size = len(s)
    i = 0

    while i < size:
        char = s[i]
        if char == "(":
            open_parens += 1
        elif char == ")":
            open_parens -= 1
        else:
            if open_parens == 0:
                if char == "+":
                    tokens.append(token(i, Operations.OR))
                elif char == "*":
                    tokens.append(token(i, Operations.AND))
                elif char == "-" and i < size - 1 and s[i + 1] == ">":
                    tokens.append(token(i, Operations.IMPLIES, end=i + 1))
                elif char == "<" and i < size - 2 and s[i : i + 3] == "<->":
                    tokens.append(token(i, Operations.DUAL_IMPLICATION, end=i + 2))
                    i += 1
                elif char == "~":
                    tokens.append(token(i, Operations.NOT))
        i += 1

    return tokens


def token(start: int, score: int, end: int = None):
    if end is None:
        end = start

    return {"start": start, "end": end, "score": score}


def left_and_right(s: str, token):
    return s[: token["start"]], right_side(s, token)


def right_side(s: str, token):
    return s[token["end"] + 1 :]


def least_precedence(tokens):
    if len(tokens) == 0:
        return -1

    i_max = 0
    i = 0

    while i < len(tokens):
        M = tokens[i_max]["score"].value
        token_scr = tokens[i]["score"].value

        if token_scr > M:
            i_max = i

        i += 1

    return i_max


def rm_outer_parenthesis(s: str):
    open_parens = 0
    # tests if s is a expr like (...) or a composition of expressions
    # by an operator like (...) + (...) * (...).
    for char in s:
        if char == "(":
            open_parens += 1
        elif char == ")":
            open_parens -= 1
        else:
            if open_parens == 0:
                return s

    # if it's just a big (...) then it's safe to remove the parenthesis.
    if s[0] == "(" and s[len(s) - 1] == ")":
        return s[1 : len(s) - 1]
    return s


def _parser(expr: str, symboldict: dict, bits):
    expr = rm_outer_parenthesis(expr)
    tokens = tokenize(expr)
    last_token = least_precedence(tokens)

    if last_token < 0:
        if expr in ["T", "F"]:
            return Truth if expr == "T" else Falsity
        # if variable is already known
        if expr in symboldict:
            return symboldict[expr]

        i = bits.realloc()

        v = Variable(bits, symbol=expr, i=i)
        symboldict[expr] = v

        return v

    left_node = None
    right_node = None
    if tokens[last_token]["score"] != Operations.NOT:
        left_expr, right_expr = left_and_right(expr, tokens[last_token])

        left_expr = rm_outer_parenthesis(left_expr)
        right_expr = rm_outer_parenthesis(right_expr)

        left_node = _parser(left_expr, symboldict, bits)
        right_node = _parser(right_expr, symboldict, bits)
    else:
        right_expr = right_side(expr, tokens[last_token])
        right_expr = rm_outer_parenthesis(right_expr)

        right_node = _parser(right_expr, symboldict, bits)
    n = Node(left=left_node, right=right_node, op=tokens[last_token]["score"])
    return n


def parser(expr: str):
    symboldict = {}
    bits = Bits(0)
    return [_parser(expr, symboldict, bits), symboldict, bits]


def _optimizer(root_node: Node, used_laws: list = []):
    new_tree = root_node
    if root_node.op == Operations.OR:
        if root_node.right == Truth or root_node.left == Truth:
            if root_node.left == Truth:
                new_tree = root_node.right
            else:
                new_tree = root_node.left
            used_laws.append(Laws.DOMINANCE)
            return new_tree
    
    return new_tree


def optimizer(root_node: Node):
    used_laws = []
    new_tree = _optimizer(root_node, used_laws)
    return new_tree, used_laws


def main():
    inp = input()
    n, s, bits = parser(inp)
    table = []
    tab_rich = Table()
    i = 0
    table = []
    for var in s:
        tab_rich.add_column(var, justify="center")
        table.append(s[var])

    tab_rich.add_column(n.to_expr(), justify="center")
    for i in range(0, 2 ** len(s)):
        tab_rich.add_row(*get_truth_row(table), str(n.get())[0])
        bits + 1

    console = Console()
    console.print(tab_rich)


def optimizer_test():
    n, s, bits = parser(input())
    print(optimizer(n).to_expr())


#optimizer_test()
main()

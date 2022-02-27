from typing import Dict, List

from lang.instruction_types import (
    And,
    BoolPush,
    CharNewLinePrint,
    Divide,
    Drop,
    Dup,
    Equals,
    Instruction,
    IntGreaterEquals,
    IntGreaterThan,
    IntLessEquals,
    IntLessThan,
    IntNotEqual,
    IntPush,
    Minus,
    Modulo,
    Multiply,
    Not,
    Or,
    Over,
    Plus,
    Print,
    Rot,
    StringLength,
    StringPush,
    SubString,
    Swap,
)
from lang.parse import (
    AaaTreeNode,
    BooleanLiteral,
    Branch,
    File,
    Function,
    FunctionBody,
    Identifier,
    IntegerLiteral,
    Loop,
    Operator,
    StringLiteral,
)

OPERATOR_INSTRUCTIONS: Dict[str, Instruction] = {
    "+": Plus(),
    "-": Minus(),
    "*": Multiply(),
    "/": Divide(),
    "%": Modulo(),
    "and": And(),
    "or": Or(),
    "not": Not(),
    "equals": Equals(),
    ">": IntGreaterThan(),
    ">=": IntGreaterEquals(),
    "<": IntLessThan(),
    "<=": IntLessEquals(),
    "!=": IntNotEqual(),
    "drop": Drop(),
    "dup": Dup(),
    "swap": Swap(),
    "over": Over(),
    "rot": Rot(),
    "\\n": CharNewLinePrint(),
    ".": Print(),
    "substr": SubString(),
    "strlen": StringLength(),
}


def get_instructions(function: Function) -> List[Instruction]:
    return _get_instructions(function, 0)


def _get_instructions(node: AaaTreeNode, offset: int) -> List[Instruction]:
    if isinstance(node, IntegerLiteral):
        return [IntPush(node.value)]

    elif isinstance(node, StringLiteral):
        return [StringPush(node.value)]

    elif isinstance(node, BooleanLiteral):
        return [BoolPush(node.value)]

    elif isinstance(node, Operator):
        raise NotImplementedError

    elif isinstance(node, Loop):
        raise NotImplementedError

    elif isinstance(node, Identifier):
        raise NotImplementedError

    elif isinstance(node, Branch):
        raise NotImplementedError

    elif isinstance(node, FunctionBody):
        raise NotImplementedError

    elif isinstance(node, Function):
        return _get_instructions(node.body, offset)

    elif isinstance(node, File):  # pragma: nocover
        # A file has no instructions.
        raise NotImplementedError

    else:  # pragma: nocover
        raise NotImplementedError

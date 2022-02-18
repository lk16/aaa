from typing import Dict, List

from lang.exceptions import ParseError
from lang.operations import (
    And,
    BoolPrint,
    BoolPush,
    Divide,
    Drop,
    Dup,
    IntEquals,
    IntGreaterEquals,
    IntGreaterThan,
    IntLessEquals,
    IntLessThan,
    IntNotEqual,
    IntPrint,
    IntPush,
    Minus,
    Multiply,
    Not,
    Operation,
    Or,
    Over,
    Plus,
    Rot,
    Swap,
)


def parse(code: str) -> List[Operation]:
    operations: List[Operation] = []
    for word in code.split():
        operation: Operation

        simple_operations: Dict[str, Operation] = {
            "int_print": IntPrint(),
            "+": Plus(),
            "-": Minus(),
            "*": Multiply(),
            "/": Divide(),
            "true": BoolPush(True),
            "false": BoolPush(False),
            "and": And(),
            "or": Or(),
            "not": Not(),
            "bool_print": BoolPrint(),
            "=": IntEquals(),
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
        }

        if word in simple_operations:
            operation = simple_operations[word]
        elif word.isdigit():
            operation = IntPush(int(word))
        else:
            raise ParseError(f"Syntax error: can't handle '{code}'")
        operations.append(operation)

    return operations

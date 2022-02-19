from typing import Dict, List

from lang.exceptions import (
    BlockStackNotEmpty,
    InvalidBlockStackValue,
    SyntaxException,
    UnexpectedOperation,
)
from lang.operations import (
    And,
    BoolPrint,
    BoolPush,
    CharNewLinePrint,
    Divide,
    Drop,
    Dup,
    Else,
    End,
    If,
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

    # Stack of indexes in block start operations (such as If) in the operations list
    block_operations_offset_stack: List[int] = []

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
            "\\n": CharNewLinePrint(),
        }

        if word in simple_operations:
            operation = simple_operations[word]

        elif word == "if":
            operation = If(None)
            block_operations_offset_stack.append(len(operations))

        elif word == "else":
            operation = Else(None)

            try:
                block_start_offset = block_operations_offset_stack.pop()
            except IndexError as e:
                # end without matching start block
                raise UnexpectedOperation(operation) from e

            block_start = operations[block_start_offset]

            if isinstance(block_start, If):
                block_start.jump_if_false = len(operations)

            else:  # pragma: nocover
                raise InvalidBlockStackValue(block_start)

            block_operations_offset_stack.append(len(operations))

        elif word == "end":
            operation = End()

            try:
                block_start_offset = block_operations_offset_stack.pop()
            except IndexError as e:
                # end without matching start block
                raise UnexpectedOperation(operation) from e

            block_start = operations[block_start_offset]

            if isinstance(block_start, If):
                block_start.jump_if_false = len(operations)

            elif isinstance(block_start, Else):
                block_start.jump_end = len(operations)
                pass

            else:  # pragma: nocover
                raise InvalidBlockStackValue(block_start)

        elif word.isdigit():
            operation = IntPush(int(word))

        else:
            raise SyntaxException(word)

        operations.append(operation)

    if block_operations_offset_stack:
        raise BlockStackNotEmpty

    return operations

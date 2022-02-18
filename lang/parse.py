from typing import Dict, List

from lang.exceptions import ParseError
from lang.operations import Divide, Minus, Multiply, Operation, Plus, PrintInt, PushInt


def parse(code: str) -> List[Operation]:
    operations: List[Operation] = []
    for word in code.split():
        operation: Operation

        simple_operations: Dict[str, Operation] = {
            "print_int": PrintInt(),
            "+": Plus(),
            "-": Minus(),
            "*": Multiply(),
            "/": Divide(),
        }

        if word in simple_operations:
            operation = simple_operations[word]
        elif word.isdigit():
            operation = PushInt(int(word))
        else:
            raise ParseError(f"Syntax error: can't handle '{code}'")
        operations.append(operation)

    return operations

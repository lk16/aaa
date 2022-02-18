from typing import List

from lang.operations import Operation, PrintInt, PushInt


def parse(code: str) -> List[Operation]:
    operations: List[Operation] = []
    for word in code.split():
        operation: Operation
        if word == "print_int":
            operation = PrintInt()
        elif word.isdigit():
            operation = PushInt(int(word))
        else:
            raise ValueError(f"Syntax error: can't handle '{code}'")
        operations.append(operation)

    return operations

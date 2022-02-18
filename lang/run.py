from typing import Any, List

from lang.operations import Operation, PrintInt, PushInt


def run_program(operations: List[Operation]) -> None:
    next_operation_index = 0
    stack: List[Any] = []

    while next_operation_index < len(operations):
        operation = operations[next_operation_index]
        if isinstance(operation, PushInt):
            stack.append(operation.value)
            next_operation_index += 1
        elif isinstance(operation, PrintInt):
            value = stack.pop()
            print(value)
            next_operation_index += 1
        else:
            raise ValueError(f"Unhandled operation {type(operation)}")

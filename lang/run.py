from typing import List

from lang.exceptions import StackUnderflow, UnhandledOperationError
from lang.operations import Operation, PrintInt, PushInt


def run_program(operations: List[Operation]) -> None:
    Program(operations).run()


StackItem = int


class Program:
    def __init__(self, operations: List[Operation]) -> None:
        self.operations = operations
        self.stack: List[StackItem] = []
        self.instruction_pointer = 0

    def push(self, item: StackItem) -> None:
        self.stack.append(item)

    def pop(self) -> StackItem:
        try:
            return self.stack.pop()
        except IndexError as e:
            raise StackUnderflow from e

    def run(self) -> None:
        while self.instruction_pointer < len(self.operations):
            operation = self.operations[self.instruction_pointer]

            if isinstance(operation, PushInt):
                self.push(operation.value)
                self.instruction_pointer += 1

            elif isinstance(operation, PrintInt):
                print(self.pop(), end="")
                self.instruction_pointer += 1

            else:  # pragma: nocover
                raise UnhandledOperationError(operation)

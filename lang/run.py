from typing import List

from lang.exceptions import StackUnderflow, UnhandledOperationError
from lang.operations import Divide, IntPush, Minus, Multiply, Operation, Plus, PrintInt


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

            if isinstance(operation, IntPush):
                self.push(operation.value)
                self.instruction_pointer += 1

            elif isinstance(operation, PrintInt):
                x = self.pop()
                print(x, end="")
                self.instruction_pointer += 1

            elif isinstance(operation, Plus):
                x = self.pop()
                y = self.pop()
                self.push(x + y)
                self.instruction_pointer += 1

            elif isinstance(operation, Minus):
                x = self.pop()
                y = self.pop()
                self.push(y - x)
                self.instruction_pointer += 1

            elif isinstance(operation, Multiply):
                x = self.pop()
                y = self.pop()
                self.push(x * y)
                self.instruction_pointer += 1

            elif isinstance(operation, Divide):
                x = self.pop()
                y = self.pop()
                self.push(y // x)
                self.instruction_pointer += 1

            else:  # pragma: nocover
                raise UnhandledOperationError(operation)

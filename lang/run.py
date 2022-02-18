from typing import List, Union

from lang.exceptions import StackUnderflow, UnhandledOperationError
from lang.operations import (
    And,
    BoolPrint,
    BoolPush,
    Divide,
    IntPrint,
    IntPush,
    Minus,
    Multiply,
    Not,
    Operation,
    Or,
    Plus,
)


def run_program(operations: List[Operation]) -> None:
    Program(operations).run()


StackItem = Union[int, bool]


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

            elif isinstance(operation, IntPrint):
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

            elif isinstance(operation, BoolPush):
                self.push(operation.value)
                self.instruction_pointer += 1

            elif isinstance(operation, And):
                x = self.pop()
                y = self.pop()
                self.push(x and y)
                self.instruction_pointer += 1

            elif isinstance(operation, Or):
                x = self.pop()
                y = self.pop()
                self.push(x or y)
                self.instruction_pointer += 1

            elif isinstance(operation, Not):
                x = self.pop()
                self.push(not x)
                self.instruction_pointer += 1

            elif isinstance(operation, BoolPrint):
                x = self.pop()
                if x:
                    print("true", end="")
                else:
                    print("false", end="")
                self.instruction_pointer += 1

            else:  # pragma: nocover
                raise UnhandledOperationError(operation)

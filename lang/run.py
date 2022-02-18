from typing import List, Tuple, Union

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

    def pop_two(self) -> Tuple[StackItem, StackItem]:
        return self.pop(), self.pop()

    def run(self) -> None:
        # NOTE This wIll be set to false by future jump operations like if/else/while
        increment_instruction_pointer = True

        while self.instruction_pointer < len(self.operations):
            operation = self.operations[self.instruction_pointer]

            if isinstance(operation, IntPush):
                self.push(operation.value)

            elif isinstance(operation, IntPrint):
                x = self.pop()
                print(x, end="")

            elif isinstance(operation, Plus):
                x, y = self.pop_two()
                self.push(x + y)

            elif isinstance(operation, Minus):
                x, y = self.pop_two()
                self.push(y - x)

            elif isinstance(operation, Multiply):
                x, y = self.pop_two()
                self.push(x * y)

            elif isinstance(operation, Divide):
                x, y = self.pop_two()
                self.push(y // x)

            elif isinstance(operation, BoolPush):
                self.push(operation.value)

            elif isinstance(operation, And):
                x, y = self.pop_two()
                self.push(x and y)

            elif isinstance(operation, Or):
                x, y = self.pop_two()
                self.push(x or y)

            elif isinstance(operation, Not):
                x = self.pop()
                self.push(not x)

            elif isinstance(operation, BoolPrint):
                x = self.pop()
                if x:
                    print("true", end="")
                else:
                    print("false", end="")

            else:  # pragma: nocover
                raise UnhandledOperationError(operation)

            if increment_instruction_pointer:
                self.instruction_pointer += 1

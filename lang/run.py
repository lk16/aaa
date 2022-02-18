from typing import List, Tuple, Union

from lang.exceptions import StackUnderflow, UnhandledOperationError
from lang.operations import (
    And,
    BoolPrint,
    BoolPush,
    Divide,
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

    def pop(self, expected_type: type) -> StackItem:
        try:
            item = self.stack.pop()
        except IndexError as e:
            raise StackUnderflow from e

        # TODO: remove type checking here once we have static type checking
        if type(item) != expected_type:
            raise TypeError(
                f"Expected {expected_type.__name__} on top of stack, but found {type(item).__name__}"
            )

        return item

    def pop_two(self, expected_type: type) -> Tuple[StackItem, StackItem]:
        return self.pop(expected_type), self.pop(expected_type)

    def run(self) -> None:  # noqa: C901  # allow high complexity of this function

        # NOTE This wIll be set to false by future jump operations like if/else/while
        increment_instruction_pointer = True

        while self.instruction_pointer < len(self.operations):
            operation = self.operations[self.instruction_pointer]

            if isinstance(operation, IntPush):
                self.push(operation.value)

            elif isinstance(operation, IntPrint):
                x = self.pop(int)
                print(x, end="")

            elif isinstance(operation, Plus):
                x, y = self.pop_two(int)
                self.push(x + y)

            elif isinstance(operation, Minus):
                x, y = self.pop_two(int)
                self.push(y - x)

            elif isinstance(operation, Multiply):
                x, y = self.pop_two(int)
                self.push(x * y)

            elif isinstance(operation, Divide):
                x, y = self.pop_two(int)
                self.push(y // x)

            elif isinstance(operation, BoolPush):
                self.push(operation.value)

            elif isinstance(operation, And):
                x, y = self.pop_two(bool)
                self.push(x and y)

            elif isinstance(operation, Or):
                x, y = self.pop_two(bool)
                self.push(x or y)

            elif isinstance(operation, Not):
                x = self.pop(bool)
                self.push(not x)

            elif isinstance(operation, BoolPrint):
                x = self.pop(bool)
                if x:
                    print("true", end="")
                else:
                    print("false", end="")

            elif isinstance(operation, IntEquals):
                x, y = self.pop_two(int)
                self.push(x == y)

            elif isinstance(operation, IntLessThan):
                x, y = self.pop_two(int)
                self.push(y < x)

            elif isinstance(operation, IntLessEquals):
                x, y = self.pop_two(int)
                self.push(y <= x)

            elif isinstance(operation, IntGreaterThan):
                x, y = self.pop_two(int)
                self.push(y > x)

            elif isinstance(operation, IntGreaterEquals):
                x, y = self.pop_two(int)
                self.push(y >= x)

            elif isinstance(operation, IntNotEqual):
                x, y = self.pop_two(int)
                self.push(y != x)

            else:
                raise UnhandledOperationError(operation)

            if increment_instruction_pointer:
                self.instruction_pointer += 1

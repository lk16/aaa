from typing import List, Tuple, Union

from lang.exceptions import (
    InvalidJump,
    StackUnderflow,
    UnexpectedType,
    UnhandledOperationError,
)
from lang.operations import (
    And,
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
    IntPush,
    Minus,
    Multiply,
    Not,
    Operation,
    Or,
    Over,
    Plus,
    Print,
    Rot,
    Swap,
)


def run_program(operations: List[Operation]) -> None:
    Program(operations).run()


StackItem = Union[int, bool]


class Program:
    def __init__(self, operations: List[Operation]) -> None:
        self.operations = operations
        self.stack: List[StackItem] = []
        self.instruction_pointer = 0

    def top_untyped(self) -> StackItem:
        try:
            return self.stack[-1]
        except IndexError as e:
            raise StackUnderflow from e

    def push(self, item: StackItem) -> None:
        self.stack.append(item)

    def pop_untyped(self) -> StackItem:
        try:
            return self.stack.pop()
        except IndexError as e:
            raise StackUnderflow from e

    def pop(self, expected_type: type) -> StackItem:
        item = self.pop_untyped()

        # TODO: remove type checking here once we have static type checking
        if type(item) != expected_type:
            raise UnexpectedType(
                f"expected {expected_type.__name__} on top of stack, but found {type(item).__name__}"
            )

        return item

    def pop_two(self, expected_type: type) -> Tuple[StackItem, StackItem]:
        return self.pop(expected_type), self.pop(expected_type)

    def run(self) -> None:  # noqa: C901  # allow high complexity of this function

        while self.instruction_pointer < len(self.operations):
            operation = self.operations[self.instruction_pointer]

            if isinstance(operation, IntPush):
                self.push(operation.value)

            elif isinstance(operation, Plus):
                z, y = self.pop_two(int)
                self.push(z + y)

            elif isinstance(operation, Minus):
                z, y = self.pop_two(int)
                self.push(y - z)

            elif isinstance(operation, Multiply):
                z, y = self.pop_two(int)
                self.push(z * y)

            elif isinstance(operation, Divide):
                z, y = self.pop_two(int)
                self.push(y // z)

            elif isinstance(operation, BoolPush):
                self.push(operation.value)

            elif isinstance(operation, And):
                z, y = self.pop_two(bool)
                self.push(z and y)

            elif isinstance(operation, Or):
                z, y = self.pop_two(bool)
                self.push(z or y)

            elif isinstance(operation, Not):
                z = self.pop(bool)
                self.push(not z)

            elif isinstance(operation, IntEquals):
                z, y = self.pop_two(int)
                self.push(z == y)

            elif isinstance(operation, IntLessThan):
                z, y = self.pop_two(int)
                self.push(y < z)

            elif isinstance(operation, IntLessEquals):
                z, y = self.pop_two(int)
                self.push(y <= z)

            elif isinstance(operation, IntGreaterThan):
                z, y = self.pop_two(int)
                self.push(y > z)

            elif isinstance(operation, IntGreaterEquals):
                z, y = self.pop_two(int)
                self.push(y >= z)

            elif isinstance(operation, IntNotEqual):
                z, y = self.pop_two(int)
                self.push(y != z)

            elif isinstance(operation, Drop):
                self.pop_untyped()

            elif isinstance(operation, Dup):
                z = self.top_untyped()
                self.push(z)

            elif isinstance(operation, Swap):
                z = self.pop_untyped()
                y = self.pop_untyped()
                self.push(z)
                self.push(y)

            elif isinstance(operation, Over):
                z = self.pop_untyped()
                y = self.top_untyped()
                self.push(z)
                self.push(y)

            elif isinstance(operation, Rot):
                x = self.pop_untyped()
                y = self.pop_untyped()
                z = self.pop_untyped()
                self.push(y)
                self.push(x)
                self.push(z)

            elif isinstance(operation, If):
                x = self.pop(bool)

                if operation.jump_if_false is None:
                    raise InvalidJump

                if not x:
                    self.instruction_pointer = operation.jump_if_false

            elif isinstance(operation, End):
                # End of block doesn't do anything
                pass

            elif isinstance(operation, Else):
                # When jumping to an jump_if_false from an If, we don't actually execute this Else.
                # This is because we advance the instruction pointer at the end of this big loop.
                # So the only way to actually hit an Else operation is by finishing the preceding If block.
                # That means we can jump to the corresponding End (which we don't execute either for the same reason).
                if operation.jump_end is None:
                    raise InvalidJump

                self.instruction_pointer = operation.jump_end

            elif isinstance(operation, CharNewLinePrint):
                # Just print a newline
                print()

            elif isinstance(operation, Print):
                x = self.pop_untyped()
                if type(x) == bool:
                    if x:
                        print("true", end="")
                    else:
                        print("false", end="")
                else:
                    print(x, end="")

            else:
                raise UnhandledOperationError(operation)

            self.instruction_pointer += 1

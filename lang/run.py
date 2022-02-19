import sys
from typing import List, Tuple, Union

from lang.exceptions import (
    InvalidJump,
    StackNotEmptyAtExit,
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
    While,
    WhileEnd,
)


def run_program(operations: List[Operation], verbose: bool = False) -> None:
    Program(operations).run(verbose=verbose)


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

    def run(  # noqa: C901  # allow high complexity of this function
        self, verbose: bool
    ) -> None:

        if verbose:  # pragma: nocover
            for ip, operation in enumerate(self.operations):
                print(f"DEBUG | IP: {ip:>2} | {operation.__repr__()}", file=sys.stderr)

            print(
                f"\nDEBUG | {'':>25} | IP: {self.instruction_pointer:>2} | Stack: "
                + " ".join(str(item) for item in self.stack),
                file=sys.stderr,
            )

        while self.instruction_pointer < len(self.operations):

            operation = self.operations[self.instruction_pointer]

            if isinstance(operation, IntPush):
                self.push(operation.value)
                self.instruction_pointer += 1

            elif isinstance(operation, Plus):
                z, y = self.pop_two(int)
                self.push(z + y)
                self.instruction_pointer += 1

            elif isinstance(operation, Minus):
                z, y = self.pop_two(int)
                self.push(y - z)
                self.instruction_pointer += 1

            elif isinstance(operation, Multiply):
                z, y = self.pop_two(int)
                self.push(z * y)
                self.instruction_pointer += 1

            elif isinstance(operation, Divide):
                z, y = self.pop_two(int)
                self.push(y // z)
                self.instruction_pointer += 1

            elif isinstance(operation, BoolPush):
                self.push(operation.value)
                self.instruction_pointer += 1

            elif isinstance(operation, And):
                z, y = self.pop_two(bool)
                self.push(z and y)
                self.instruction_pointer += 1

            elif isinstance(operation, Or):
                z, y = self.pop_two(bool)
                self.push(z or y)
                self.instruction_pointer += 1

            elif isinstance(operation, Not):
                z = self.pop(bool)
                self.push(not z)
                self.instruction_pointer += 1

            elif isinstance(operation, IntEquals):
                z, y = self.pop_two(int)
                self.push(z == y)
                self.instruction_pointer += 1

            elif isinstance(operation, IntLessThan):
                z, y = self.pop_two(int)
                self.push(y < z)
                self.instruction_pointer += 1

            elif isinstance(operation, IntLessEquals):
                z, y = self.pop_two(int)
                self.push(y <= z)
                self.instruction_pointer += 1

            elif isinstance(operation, IntGreaterThan):
                z, y = self.pop_two(int)
                self.push(y > z)
                self.instruction_pointer += 1

            elif isinstance(operation, IntGreaterEquals):
                z, y = self.pop_two(int)
                self.push(y >= z)
                self.instruction_pointer += 1

            elif isinstance(operation, IntNotEqual):
                z, y = self.pop_two(int)
                self.push(y != z)
                self.instruction_pointer += 1

            elif isinstance(operation, Drop):
                self.pop_untyped()
                self.instruction_pointer += 1

            elif isinstance(operation, Dup):
                z = self.top_untyped()
                self.push(z)
                self.instruction_pointer += 1

            elif isinstance(operation, Swap):
                z = self.pop_untyped()
                y = self.pop_untyped()
                self.push(z)
                self.push(y)
                self.instruction_pointer += 1

            elif isinstance(operation, Over):
                z = self.pop_untyped()
                y = self.top_untyped()
                self.push(z)
                self.push(y)
                self.instruction_pointer += 1

            elif isinstance(operation, Rot):
                x = self.pop_untyped()
                y = self.pop_untyped()
                z = self.pop_untyped()
                self.push(y)
                self.push(x)
                self.push(z)
                self.instruction_pointer += 1

            elif isinstance(operation, If):
                x = self.pop(bool)

                # TODO move this check to parse
                if operation.jump_if_false is None:
                    raise InvalidJump

                if not x:
                    self.instruction_pointer = operation.jump_if_false

                self.instruction_pointer += 1

            elif isinstance(operation, End):
                # End of block doesn't do anything
                self.instruction_pointer += 1

            elif isinstance(operation, Else):
                # TODO move this check to parse
                if operation.jump_end is None:
                    raise InvalidJump

                # Jump beyond the else instruction
                self.instruction_pointer = operation.jump_end + 1

            elif isinstance(operation, CharNewLinePrint):
                print()  # Just print a newline
                self.instruction_pointer += 1

            elif isinstance(operation, Print):
                x = self.pop_untyped()
                if type(x) == bool:
                    if x:
                        print("true", end="")
                    else:
                        print("false", end="")
                else:
                    print(x, end="")

                self.instruction_pointer += 1

            elif isinstance(operation, While):
                x = self.pop(bool)

                # TODO move this check to parse
                if operation.jump_end is None:
                    raise InvalidJump

                if not x:
                    self.instruction_pointer = operation.jump_end

                self.instruction_pointer += 1

            elif isinstance(operation, WhileEnd):
                self.instruction_pointer = operation.jump_start

            else:
                raise UnhandledOperationError(operation)

            if verbose:  # pragma: nocover
                print(
                    f"DEBUG | {operation.__repr__():>25} | IP: {self.instruction_pointer:>2} | Stack: "
                    + " ".join(str(item) for item in self.stack),
                    file=sys.stderr,
                )

        if self.stack:
            raise StackNotEmptyAtExit

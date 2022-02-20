import sys
from typing import Dict, List, Tuple, Union

from lang.exceptions import (
    StackNotEmptyAtExit,
    StackUnderflow,
    UnexpectedType,
    UnhandledOperationError,
)
from lang.types import (
    And,
    BoolPush,
    CharNewLinePrint,
    Divide,
    Drop,
    Dup,
    Else,
    End,
    Equals,
    Function,
    If,
    IntGreaterEquals,
    IntGreaterThan,
    IntLessEquals,
    IntLessThan,
    IntNotEqual,
    IntPush,
    Minus,
    Modulo,
    Multiply,
    Not,
    Or,
    Over,
    Plus,
    Print,
    Rot,
    StringLength,
    StringPush,
    SubString,
    Swap,
    While,
    WhileEnd,
)

StackItem = Union[int, bool, str]


class Program:
    def __init__(self, functions: Dict[str, Function]) -> None:
        self.functions = functions
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

    def check_type(self, item: StackItem, expected_types: List[type]) -> None:
        # TODO: remove type checking here once we have static type checking
        if type(item) not in expected_types:
            raise UnexpectedType(
                "expected "
                + " or ".join(
                    expected_type.__name__ for expected_type in expected_types
                )
                + f" on top of stack, but found {type(item).__name__}"
            )

    def pop(self, expected_type: type) -> StackItem:
        item = self.pop_untyped()
        self.check_type(item, [expected_type])

        return item

    def pop_two(self, expected_type: type) -> Tuple[StackItem, StackItem]:
        return self.pop(expected_type), self.pop(expected_type)

    def run(self, verbose: bool) -> None:
        self.run_function("main", verbose)

    def run_function(  # noqa: C901  # allow high complexity of this function
        self, func_name: str, verbose: bool
    ) -> None:
        operations = self.functions[func_name].operations

        # TODO deal with function arguments

        if verbose:  # pragma: nocover
            for ip, operation in enumerate(operations):
                print(f"DEBUG | IP: {ip:>2} | {operation.__repr__()}", file=sys.stderr)

            print(
                f"\nDEBUG | {'':>25} | IP: {self.instruction_pointer:>2} | Stack: "
                + " ".join(str(item) for item in self.stack),
                file=sys.stderr,
            )

        while self.instruction_pointer < len(operations):

            operation = operations[self.instruction_pointer]

            # TODO rewrite this entire if-else chain as dictionary

            if isinstance(operation, IntPush):
                self.push(operation.value)
                self.instruction_pointer += 1

            elif isinstance(operation, Plus):
                x = self.pop_untyped()
                y = self.pop_untyped()
                self.check_type(x, [int, str])
                self.check_type(y, [type(x)])

                self.push(y + x)  # type: ignore
                self.instruction_pointer += 1

            elif isinstance(operation, Minus):
                x, y = self.pop_two(int)
                self.push(y - x)  # type: ignore
                self.instruction_pointer += 1

            elif isinstance(operation, Multiply):
                x, y = self.pop_two(int)
                self.push(x * y)  # type: ignore
                self.instruction_pointer += 1

            elif isinstance(operation, Divide):
                x, y = self.pop_two(int)
                self.push(y // x)  # type: ignore
                self.instruction_pointer += 1

            elif isinstance(operation, Modulo):
                x, y = self.pop_two(int)
                self.push(y % x)  # type: ignore
                self.instruction_pointer += 1

            elif isinstance(operation, BoolPush):
                self.push(operation.value)
                self.instruction_pointer += 1

            elif isinstance(operation, And):
                x, y = self.pop_two(bool)
                self.push(x and y)
                self.instruction_pointer += 1

            elif isinstance(operation, Or):
                x, y = self.pop_two(bool)
                self.push(x or y)
                self.instruction_pointer += 1

            elif isinstance(operation, Not):
                x = self.pop(bool)
                self.push(not x)
                self.instruction_pointer += 1

            elif isinstance(operation, Equals):
                x = self.pop_untyped()
                y = self.pop_untyped()
                self.check_type(x, [int, str])
                self.check_type(y, [type(x)])

                self.push(x == y)
                self.instruction_pointer += 1

            elif isinstance(operation, IntLessThan):
                x, y = self.pop_two(int)
                self.push(y < x)  # type: ignore
                self.instruction_pointer += 1

            elif isinstance(operation, IntLessEquals):
                x, y = self.pop_two(int)
                self.push(y <= x)  # type: ignore
                self.instruction_pointer += 1

            elif isinstance(operation, IntGreaterThan):
                x, y = self.pop_two(int)
                self.push(y > x)  # type: ignore
                self.instruction_pointer += 1

            elif isinstance(operation, IntGreaterEquals):
                x, y = self.pop_two(int)
                self.push(y >= x)  # type: ignore
                self.instruction_pointer += 1

            elif isinstance(operation, IntNotEqual):
                x, y = self.pop_two(int)
                self.push(y != x)
                self.instruction_pointer += 1

            elif isinstance(operation, Drop):
                self.pop_untyped()
                self.instruction_pointer += 1

            elif isinstance(operation, Dup):
                x = self.top_untyped()
                self.push(x)
                self.instruction_pointer += 1

            elif isinstance(operation, Swap):
                x = self.pop_untyped()
                y = self.pop_untyped()
                self.push(x)
                self.push(y)
                self.instruction_pointer += 1

            elif isinstance(operation, Over):
                x = self.pop_untyped()
                y = self.top_untyped()
                self.push(x)
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

                if not x:
                    assert (
                        operation.jump_if_false is not None
                    )  # nosec  # This is checked while parsing
                    self.instruction_pointer = operation.jump_if_false

                self.instruction_pointer += 1

            elif isinstance(operation, End):
                # End of block doesn't do anything
                self.instruction_pointer += 1

            elif isinstance(operation, Else):
                assert (
                    operation.jump_end is not None
                )  # nosec  # This is checked while parsing

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

                if not x:
                    assert (
                        operation.jump_end is not None
                    )  # nosec  # This is checked while parsing
                    self.instruction_pointer = operation.jump_end

                self.instruction_pointer += 1

            elif isinstance(operation, WhileEnd):
                self.instruction_pointer = operation.jump_start

            elif isinstance(operation, StringPush):
                self.push(operation.value)
                self.instruction_pointer += 1

            elif isinstance(operation, SubString):
                end: int = self.pop(int)  # type: ignore
                start: int = self.pop(int)  # type: ignore
                string: str = self.pop(str)  # type: ignore

                if start >= end or start > len(string):
                    self.push("")
                else:
                    self.push(string[start:end])

                self.instruction_pointer += 1

            elif isinstance(operation, StringLength):
                x = self.pop(str)
                self.push(len(x))  # type: ignore
                self.instruction_pointer += 1

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

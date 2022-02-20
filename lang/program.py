import sys
from typing import Callable, Dict, List, Tuple, Type, Union

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
    Operation,
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

        operation_funcs: Dict[Type[Operation], Callable[[Operation], None]] = {
            And: self.op_and,
            BoolPush: self.op_boolPush,
            CharNewLinePrint: self.op_char_newline_print,
            Divide: self.op_divide,
            Drop: self.op_drop,
            Dup: self.op_dup,
            Else: self.op_else,
            End: self.op_end,
            Equals: self.op_equals,
            If: self.op_if,
            IntGreaterEquals: self.op_int_greater_equals,
            IntGreaterThan: self.op_int_greater_than,
            IntLessEquals: self.op_int_less_equals,
            IntLessThan: self.op_int_less_than,
            IntNotEqual: self.op_int_not_equal,
            IntPush: self.op_int_push,
            Minus: self.op_minus,
            Modulo: self.op_modulo,
            Multiply: self.op_multiply,
            Not: self.op_not,
            Or: self.op_or,
            Over: self.op_over,
            Plus: self.op_plus,
            Print: self.op_print,
            Rot: self.op_rot,
            StringLength: self.op_string_length,
            StringPush: self.op_string_push,
            SubString: self.op_substring,
            Swap: self.op_swap,
            While: self.op_while,
            WhileEnd: self.op_while_end,
        }

        while self.instruction_pointer < len(operations):

            # Find out what the next operation is
            operation = operations[self.instruction_pointer]

            # Excecute the operation
            try:
                operation_func = operation_funcs[type(operation)]
            except KeyError as e:
                raise UnhandledOperationError(operation) from e

            operation_func(operation)

            if verbose:  # pragma: nocover
                print(
                    f"DEBUG | {operation.__repr__():>25} | IP: {self.instruction_pointer:>2} | Stack: "
                    + " ".join(str(item) for item in self.stack),
                    file=sys.stderr,
                )

        if self.stack:
            raise StackNotEmptyAtExit

    def op_int_push(self, operation: Operation) -> None:
        assert isinstance(operation, IntPush)  # nosec
        self.push(operation.value)
        self.instruction_pointer += 1

    def op_plus(self, operation: Operation) -> None:
        assert isinstance(operation, Plus)  # nosec
        x = self.pop_untyped()
        y = self.pop_untyped()
        self.check_type(x, [int, str])
        self.check_type(y, [type(x)])

        self.push(y + x)  # type: ignore
        self.instruction_pointer += 1

    def op_minus(self, operation: Operation) -> None:
        assert isinstance(operation, Minus)  # nosec
        x, y = self.pop_two(int)
        self.push(y - x)  # type: ignore
        self.instruction_pointer += 1

    def op_multiply(self, operation: Operation) -> None:
        assert isinstance(operation, Multiply)  # nosec
        x, y = self.pop_two(int)
        self.push(x * y)  # type: ignore
        self.instruction_pointer += 1

    def op_divide(self, operation: Operation) -> None:
        assert isinstance(operation, Divide)  # nosec
        x, y = self.pop_two(int)
        self.push(y // x)  # type: ignore
        self.instruction_pointer += 1

    def op_modulo(self, operation: Operation) -> None:
        assert isinstance(operation, Modulo)  # nosec
        x, y = self.pop_two(int)
        self.push(y % x)  # type: ignore
        self.instruction_pointer += 1

    def op_boolPush(self, operation: Operation) -> None:
        assert isinstance(operation, BoolPush)  # nosec
        self.push(operation.value)
        self.instruction_pointer += 1

    def op_and(self, operation: Operation) -> None:
        assert isinstance(operation, And)  # nosec
        x, y = self.pop_two(bool)
        self.push(x and y)
        self.instruction_pointer += 1

    def op_or(self, operation: Operation) -> None:
        assert isinstance(operation, Or)  # nosec
        x, y = self.pop_two(bool)
        self.push(x or y)
        self.instruction_pointer += 1

    def op_not(self, operation: Operation) -> None:
        assert isinstance(operation, Not)  # nosec
        x = self.pop(bool)
        self.push(not x)
        self.instruction_pointer += 1

    def op_equals(self, operation: Operation) -> None:
        assert isinstance(operation, Equals)  # nosec
        x = self.pop_untyped()
        y = self.pop_untyped()
        self.check_type(x, [int, str])
        self.check_type(y, [type(x)])

        self.push(x == y)
        self.instruction_pointer += 1

    def op_int_less_than(self, operation: Operation) -> None:
        assert isinstance(operation, IntLessThan)  # nosec
        x, y = self.pop_two(int)
        self.push(y < x)  # type: ignore
        self.instruction_pointer += 1

    def op_int_less_equals(self, operation: Operation) -> None:
        assert isinstance(operation, IntLessEquals)  # nosec
        x, y = self.pop_two(int)
        self.push(y <= x)  # type: ignore
        self.instruction_pointer += 1

    def op_int_greater_than(self, operation: Operation) -> None:
        assert isinstance(operation, IntGreaterThan)  # nosec
        x, y = self.pop_two(int)
        self.push(y > x)  # type: ignore
        self.instruction_pointer += 1

    def op_int_greater_equals(self, operation: Operation) -> None:
        assert isinstance(operation, IntGreaterEquals)  # nosec
        x, y = self.pop_two(int)
        self.push(y >= x)  # type: ignore
        self.instruction_pointer += 1

    def op_int_not_equal(self, operation: Operation) -> None:
        assert isinstance(operation, IntNotEqual)  # nosec
        x, y = self.pop_two(int)
        self.push(y != x)
        self.instruction_pointer += 1

    def op_drop(self, operation: Operation) -> None:
        assert isinstance(operation, Drop)  # nosec
        self.pop_untyped()
        self.instruction_pointer += 1

    def op_dup(self, operation: Operation) -> None:
        assert isinstance(operation, Dup)  # nosec
        x = self.top_untyped()
        self.push(x)
        self.instruction_pointer += 1

    def op_swap(self, operation: Operation) -> None:
        assert isinstance(operation, Swap)  # nosec
        x = self.pop_untyped()
        y = self.pop_untyped()
        self.push(x)
        self.push(y)
        self.instruction_pointer += 1

    def op_over(self, operation: Operation) -> None:
        assert isinstance(operation, Over)  # nosec
        x = self.pop_untyped()
        y = self.top_untyped()
        self.push(x)
        self.push(y)
        self.instruction_pointer += 1

    def op_rot(self, operation: Operation) -> None:
        assert isinstance(operation, Rot)  # nosec
        x = self.pop_untyped()
        y = self.pop_untyped()
        z = self.pop_untyped()
        self.push(y)
        self.push(x)
        self.push(z)
        self.instruction_pointer += 1

    def op_if(self, operation: Operation) -> None:
        assert isinstance(operation, If)  # nosec
        x = self.pop(bool)

        if not x:
            assert (
                operation.jump_if_false is not None
            )  # nosec  # This is checked while parsing
            self.instruction_pointer = operation.jump_if_false

        self.instruction_pointer += 1

    def op_end(self, operation: Operation) -> None:
        assert isinstance(operation, End)  # nosec
        # End of block doesn't do anything
        self.instruction_pointer += 1

    def op_else(self, operation: Operation) -> None:
        assert isinstance(operation, Else)  # nosec
        assert operation.jump_end is not None  # nosec  # This is checked while parsing

        # Jump beyond the else instruction
        self.instruction_pointer = operation.jump_end + 1

    def op_char_newline_print(self, operation: Operation) -> None:
        assert isinstance(operation, CharNewLinePrint)  # nosec
        print()  # Just print a newline
        self.instruction_pointer += 1

    def op_print(self, operation: Operation) -> None:
        assert isinstance(operation, Print)  # nosec
        x = self.pop_untyped()
        if type(x) == bool:
            if x:
                print("true", end="")
            else:
                print("false", end="")
        else:
            print(x, end="")

        self.instruction_pointer += 1

    def op_while(self, operation: Operation) -> None:
        assert isinstance(operation, While)  # nosec
        x = self.pop(bool)

        if not x:
            assert (
                operation.jump_end is not None
            )  # nosec  # This is checked while parsing
            self.instruction_pointer = operation.jump_end

        self.instruction_pointer += 1

    def op_while_end(self, operation: Operation) -> None:
        assert isinstance(operation, WhileEnd)  # nosec
        self.instruction_pointer = operation.jump_start

    def op_string_push(self, operation: Operation) -> None:
        assert isinstance(operation, StringPush)  # nosec
        self.push(operation.value)
        self.instruction_pointer += 1

    def op_substring(self, operation: Operation) -> None:
        assert isinstance(operation, SubString)  # nosec
        end: int = self.pop(int)  # type: ignore
        start: int = self.pop(int)  # type: ignore
        string: str = self.pop(str)  # type: ignore

        if start >= end or start > len(string):
            self.push("")
        else:
            self.push(string[start:end])

        self.instruction_pointer += 1

    def op_string_length(self, operation: Operation) -> None:
        assert isinstance(operation, StringLength)  # nosec
        x = self.pop(str)
        self.push(len(x))  # type: ignore
        self.instruction_pointer += 1

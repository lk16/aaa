import sys
from typing import Callable, Dict, List, Tuple, Type, Union

from lang.exceptions import (
    StackNotEmptyAtExit,
    StackUnderflow,
    UnexpectedType,
    UnhandledInstructionError,
)
from lang.instructions import (
    And,
    BoolPush,
    CharNewLinePrint,
    Divide,
    Drop,
    Dup,
    Else,
    End,
    Equals,
    If,
    Instruction,
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
from lang.parse import Function

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

    def run_function(self, func_name: str, verbose: bool) -> None:

        # TODO can this cause a KeyError?
        function = self.functions[func_name]

        instructions = function.get_instructions()

        # TODO deal with function arguments

        if verbose:  # pragma: nocover
            for ip, instruction in enumerate(instructions):
                print(
                    f"DEBUG | IP: {ip:>2} | {instruction.__repr__()}", file=sys.stderr
                )

            print(
                f"\nDEBUG | {'':>25} | IP: {self.instruction_pointer:>2} | Stack: "
                + " ".join(str(item) for item in self.stack),
                file=sys.stderr,
            )

        instruction_funcs: Dict[Type[Instruction], Callable[[Instruction], None]] = {
            And: self.instruction_and,
            BoolPush: self.instruction_boolPush,
            CharNewLinePrint: self.instruction_char_newline_print,
            Divide: self.instruction_divide,
            Drop: self.instruction_drop,
            Dup: self.instruction_dup,
            Else: self.instruction_else,
            End: self.instruction_end,
            Equals: self.instruction_equals,
            If: self.instruction_if,
            IntGreaterEquals: self.instruction_int_greater_equals,
            IntGreaterThan: self.instruction_int_greater_than,
            IntLessEquals: self.instruction_int_less_equals,
            IntLessThan: self.instruction_int_less_than,
            IntNotEqual: self.instruction_int_not_equal,
            IntPush: self.instruction_int_push,
            Minus: self.instruction_minus,
            Modulo: self.instruction_modulo,
            Multiply: self.instruction_multiply,
            Not: self.instruction_not,
            Or: self.instruction_or,
            Over: self.instruction_over,
            Plus: self.instruction_plus,
            Print: self.instruction_print,
            Rot: self.instruction_rot,
            StringLength: self.instruction_string_length,
            StringPush: self.instruction_string_push,
            SubString: self.instruction_substring,
            Swap: self.instruction_swap,
            While: self.instruction_while,
            WhileEnd: self.instruction_while_end,
        }

        while self.instruction_pointer < len(instructions):

            # Find out what the next instruction is
            instruction = instructions[self.instruction_pointer]

            # Excecute the instruction
            try:
                instrunction_func = instruction_funcs[type(instruction)]
            except KeyError as e:
                raise UnhandledInstructionError(instruction) from e

            instrunction_func(instruction)

            if verbose:  # pragma: nocover
                print(
                    f"DEBUG | {instruction.__repr__():>25} | IP: {self.instruction_pointer:>2} | Stack: "
                    + " ".join(str(item) for item in self.stack),
                    file=sys.stderr,
                )

        if self.stack:
            raise StackNotEmptyAtExit

    def instruction_int_push(self, instruction: Instruction) -> None:
        assert isinstance(instruction, IntPush)
        self.push(instruction.value)
        self.instruction_pointer += 1

    def instruction_plus(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Plus)
        x = self.pop_untyped()
        y = self.pop_untyped()
        self.check_type(x, [int, str])
        self.check_type(y, [type(x)])

        self.push(y + x)  # type: ignore
        self.instruction_pointer += 1

    def instruction_minus(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Minus)
        x, y = self.pop_two(int)
        self.push(y - x)  # type: ignore
        self.instruction_pointer += 1

    def instruction_multiply(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Multiply)
        x, y = self.pop_two(int)
        self.push(x * y)  # type: ignore
        self.instruction_pointer += 1

    def instruction_divide(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Divide)
        x, y = self.pop_two(int)
        self.push(y // x)  # type: ignore
        self.instruction_pointer += 1

    def instruction_modulo(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Modulo)
        x, y = self.pop_two(int)
        self.push(y % x)  # type: ignore
        self.instruction_pointer += 1

    def instruction_boolPush(self, instruction: Instruction) -> None:
        assert isinstance(instruction, BoolPush)
        self.push(instruction.value)
        self.instruction_pointer += 1

    def instruction_and(self, instruction: Instruction) -> None:
        assert isinstance(instruction, And)
        x, y = self.pop_two(bool)
        self.push(x and y)
        self.instruction_pointer += 1

    def instruction_or(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Or)
        x, y = self.pop_two(bool)
        self.push(x or y)
        self.instruction_pointer += 1

    def instruction_not(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Not)
        x = self.pop(bool)
        self.push(not x)
        self.instruction_pointer += 1

    def instruction_equals(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Equals)
        x = self.pop_untyped()
        y = self.pop_untyped()
        self.check_type(x, [int, str])
        self.check_type(y, [type(x)])

        self.push(x == y)
        self.instruction_pointer += 1

    def instruction_int_less_than(self, instruction: Instruction) -> None:
        assert isinstance(instruction, IntLessThan)
        x, y = self.pop_two(int)
        self.push(y < x)  # type: ignore
        self.instruction_pointer += 1

    def instruction_int_less_equals(self, instruction: Instruction) -> None:
        assert isinstance(instruction, IntLessEquals)
        x, y = self.pop_two(int)
        self.push(y <= x)  # type: ignore
        self.instruction_pointer += 1

    def instruction_int_greater_than(self, instruction: Instruction) -> None:
        assert isinstance(instruction, IntGreaterThan)
        x, y = self.pop_two(int)
        self.push(y > x)  # type: ignore
        self.instruction_pointer += 1

    def instruction_int_greater_equals(self, instruction: Instruction) -> None:
        assert isinstance(instruction, IntGreaterEquals)
        x, y = self.pop_two(int)
        self.push(y >= x)  # type: ignore
        self.instruction_pointer += 1

    def instruction_int_not_equal(self, instruction: Instruction) -> None:
        assert isinstance(instruction, IntNotEqual)
        x, y = self.pop_two(int)
        self.push(y != x)
        self.instruction_pointer += 1

    def instruction_drop(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Drop)
        self.pop_untyped()
        self.instruction_pointer += 1

    def instruction_dup(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Dup)
        x = self.top_untyped()
        self.push(x)
        self.instruction_pointer += 1

    def instruction_swap(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Swap)
        x = self.pop_untyped()
        y = self.pop_untyped()
        self.push(x)
        self.push(y)
        self.instruction_pointer += 1

    def instruction_over(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Over)
        x = self.pop_untyped()
        y = self.top_untyped()
        self.push(x)
        self.push(y)
        self.instruction_pointer += 1

    def instruction_rot(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Rot)
        x = self.pop_untyped()
        y = self.pop_untyped()
        z = self.pop_untyped()
        self.push(y)
        self.push(x)
        self.push(z)
        self.instruction_pointer += 1

    def instruction_if(self, instruction: Instruction) -> None:
        assert isinstance(instruction, If)
        x = self.pop(bool)

        if not x:
            assert (
                instruction.jump_if_false is not None
            )  # This is checked while parsing
            self.instruction_pointer = instruction.jump_if_false

        self.instruction_pointer += 1

    def instruction_end(self, instruction: Instruction) -> None:
        assert isinstance(instruction, End)
        # End of block doesn't do anything
        self.instruction_pointer += 1

    def instruction_else(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Else)
        assert instruction.jump_end is not None  # This is checked while parsing

        # Jump beyond the else instruction
        self.instruction_pointer = instruction.jump_end + 1

    def instruction_char_newline_print(self, instruction: Instruction) -> None:
        assert isinstance(instruction, CharNewLinePrint)
        print()  # Just print a newline
        self.instruction_pointer += 1

    def instruction_print(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Print)
        x = self.pop_untyped()
        if type(x) == bool:
            if x:
                print("true", end="")
            else:
                print("false", end="")
        else:
            print(x, end="")

        self.instruction_pointer += 1

    def instruction_while(self, instruction: Instruction) -> None:
        assert isinstance(instruction, While)
        x = self.pop(bool)

        if not x:
            assert instruction.jump_end is not None  # This is checked while parsing
            self.instruction_pointer = instruction.jump_end

        self.instruction_pointer += 1

    def instruction_while_end(self, instruction: Instruction) -> None:
        assert isinstance(instruction, WhileEnd)
        self.instruction_pointer = instruction.jump_start

    def instruction_string_push(self, instruction: Instruction) -> None:
        assert isinstance(instruction, StringPush)
        self.push(instruction.value)
        self.instruction_pointer += 1

    def instruction_substring(self, instruction: Instruction) -> None:
        assert isinstance(instruction, SubString)
        end: int = self.pop(int)  # type: ignore
        start: int = self.pop(int)  # type: ignore
        string: str = self.pop(str)  # type: ignore

        if start >= end or start > len(string):
            self.push("")
        else:
            self.push(string[start:end])

        self.instruction_pointer += 1

    def instruction_string_length(self, instruction: Instruction) -> None:
        assert isinstance(instruction, StringLength)
        x = self.pop(str)
        self.push(len(x))  # type: ignore
        self.instruction_pointer += 1

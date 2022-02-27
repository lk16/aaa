import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple, Type, Union

from lang.exceptions import (
    StackNotEmptyAtExit,
    StackUnderflow,
    UnexpectedType,
    UnhandledInstructionError,
)
from lang.instruction_types import (
    And,
    BoolPush,
    CallFunction,
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
    PushFunctionArgument,
    Rot,
    StringLength,
    StringPush,
    SubString,
    Swap,
    While,
    WhileEnd,
)
from lang.instructions import get_instructions
from lang.parse import Function

StackItem = Union[int, bool, str]


@dataclass
class CallStackItem:
    func_name: str
    instruction_pointer: int
    argument_values: Dict[str, StackItem]


class Program:
    def __init__(self, functions: Dict[str, Function], verbose: bool = False) -> None:
        self.functions = functions
        self.stack: List[StackItem] = []
        self.call_stack: List[CallStackItem] = []
        self.verbose = verbose

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

    def get_function_argument(self, arg_name: str) -> StackItem:
        return self.call_stack[-1].argument_values[arg_name]

    def get_instruction_pointer(self) -> int:
        return self.call_stack[-1].instruction_pointer

    def advance_instruction_pointer(self) -> None:
        self.call_stack[-1].instruction_pointer += 1

    def jump(self, offset: int) -> None:
        self.call_stack[-1].instruction_pointer = offset

    def run(self) -> None:
        self.call_function("main")

        if self.stack:
            raise StackNotEmptyAtExit

    def call_function(self, func_name: str) -> None:
        # TODO deal with KeyError here
        function = self.functions[func_name]

        argument_values: Dict[str, StackItem] = {
            arg_name: self.top_untyped() for arg_name in reversed(function.arguments)
        }

        self.call_stack.append(CallStackItem(func_name, 0, argument_values))

        instructions = get_instructions(function)

        if self.verbose:  # pragma: nocover  # TODO make separate function
            for ip, instruction in enumerate(instructions):
                print(
                    f"DEBUG | IP: {ip:>2} | {instruction.__repr__()}", file=sys.stderr
                )

            print(
                f"\nDEBUG | {'':>25} | IP: {self.get_instruction_pointer:>2} | Stack: "
                + " ".join(str(item) for item in self.stack),
                file=sys.stderr,
            )

        instruction_funcs: Dict[
            Type[Instruction], Callable[[Instruction], None]
        ] = {  # TODO move out of this function
            And: self.instruction_and,
            BoolPush: self.instruction_boolPush,
            CharNewLinePrint: self.instruction_char_newline_print,
            CallFunction: self.instruction_call_function,
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
            PushFunctionArgument: self.instruction_push_function_argument,
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

        while True:
            instruction_pointer = self.get_instruction_pointer()

            if instruction_pointer >= len(instructions):
                break

            # Find out what the next instruction is
            instruction = instructions[instruction_pointer]

            # Excecute the instruction
            try:
                instrunction_func = instruction_funcs[type(instruction)]
            except KeyError as e:
                raise UnhandledInstructionError(instruction) from e

            instrunction_func(instruction)

            if self.verbose:  # pragma: nocover  # TODO make separate function
                print(
                    f"DEBUG | {instruction.__repr__():>25} | IP: {self.get_instruction_pointer:>2} | Stack: "
                    + " ".join(str(item) for item in self.stack),
                    file=sys.stderr,
                )

        if self.stack:
            raise StackNotEmptyAtExit

    def instruction_int_push(self, instruction: Instruction) -> None:
        assert isinstance(instruction, IntPush)
        self.push(instruction.value)
        self.advance_instruction_pointer()

    def instruction_plus(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Plus)
        x = self.pop_untyped()
        y = self.pop_untyped()
        self.check_type(x, [int, str])
        self.check_type(y, [type(x)])

        self.push(y + x)  # type: ignore
        self.advance_instruction_pointer()

    def instruction_minus(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Minus)
        x, y = self.pop_two(int)
        self.push(y - x)  # type: ignore
        self.advance_instruction_pointer()

    def instruction_multiply(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Multiply)
        x, y = self.pop_two(int)
        self.push(x * y)  # type: ignore
        self.advance_instruction_pointer()

    def instruction_divide(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Divide)
        x, y = self.pop_two(int)
        self.push(y // x)  # type: ignore
        self.advance_instruction_pointer()

    def instruction_modulo(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Modulo)
        x, y = self.pop_two(int)
        self.push(y % x)  # type: ignore
        self.advance_instruction_pointer()

    def instruction_boolPush(self, instruction: Instruction) -> None:
        assert isinstance(instruction, BoolPush)
        self.push(instruction.value)
        self.advance_instruction_pointer()

    def instruction_and(self, instruction: Instruction) -> None:
        assert isinstance(instruction, And)
        x, y = self.pop_two(bool)
        self.push(x and y)
        self.advance_instruction_pointer()

    def instruction_or(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Or)
        x, y = self.pop_two(bool)
        self.push(x or y)
        self.advance_instruction_pointer()

    def instruction_not(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Not)
        x = self.pop(bool)
        self.push(not x)
        self.advance_instruction_pointer()

    def instruction_equals(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Equals)
        x = self.pop_untyped()
        y = self.pop_untyped()
        self.check_type(x, [int, str])
        self.check_type(y, [type(x)])

        self.push(x == y)
        self.advance_instruction_pointer()

    def instruction_int_less_than(self, instruction: Instruction) -> None:
        assert isinstance(instruction, IntLessThan)
        x, y = self.pop_two(int)
        self.push(y < x)  # type: ignore
        self.advance_instruction_pointer()

    def instruction_int_less_equals(self, instruction: Instruction) -> None:
        assert isinstance(instruction, IntLessEquals)
        x, y = self.pop_two(int)
        self.push(y <= x)  # type: ignore
        self.advance_instruction_pointer()

    def instruction_int_greater_than(self, instruction: Instruction) -> None:
        assert isinstance(instruction, IntGreaterThan)
        x, y = self.pop_two(int)
        self.push(y > x)  # type: ignore
        self.advance_instruction_pointer()

    def instruction_int_greater_equals(self, instruction: Instruction) -> None:
        assert isinstance(instruction, IntGreaterEquals)
        x, y = self.pop_two(int)
        self.push(y >= x)  # type: ignore
        self.advance_instruction_pointer()

    def instruction_int_not_equal(self, instruction: Instruction) -> None:
        assert isinstance(instruction, IntNotEqual)
        x, y = self.pop_two(int)
        self.push(y != x)
        self.advance_instruction_pointer()

    def instruction_drop(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Drop)
        self.pop_untyped()
        self.advance_instruction_pointer()

    def instruction_dup(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Dup)
        x = self.top_untyped()
        self.push(x)
        self.advance_instruction_pointer()

    def instruction_swap(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Swap)
        x = self.pop_untyped()
        y = self.pop_untyped()
        self.push(x)
        self.push(y)
        self.advance_instruction_pointer()

    def instruction_over(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Over)
        x = self.pop_untyped()
        y = self.top_untyped()
        self.push(x)
        self.push(y)
        self.advance_instruction_pointer()

    def instruction_rot(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Rot)
        x = self.pop_untyped()
        y = self.pop_untyped()
        z = self.pop_untyped()
        self.push(y)
        self.push(x)
        self.push(z)
        self.advance_instruction_pointer()

    def instruction_if(self, instruction: Instruction) -> None:
        assert isinstance(instruction, If)
        x = self.pop(bool)

        if not x:
            self.jump(instruction.jump_if_false)

        self.advance_instruction_pointer()

    def instruction_end(self, instruction: Instruction) -> None:
        assert isinstance(instruction, End)
        # End of block doesn't do anything
        self.advance_instruction_pointer()

    def instruction_else(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Else)

        # Jump beyond the else instruction
        self.jump(
            instruction.jump_end + 1
        )  # TODO move +1 part to instruction generator

    def instruction_char_newline_print(self, instruction: Instruction) -> None:
        assert isinstance(instruction, CharNewLinePrint)
        print()  # Just print a newline
        self.advance_instruction_pointer()

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

        self.advance_instruction_pointer()

    def instruction_while(self, instruction: Instruction) -> None:
        assert isinstance(instruction, While)
        x = self.pop(bool)

        if not x:
            self.jump(instruction.jump_end)

        self.advance_instruction_pointer()

    def instruction_while_end(self, instruction: Instruction) -> None:
        assert isinstance(instruction, WhileEnd)
        self.jump(instruction.jump_start)

    def instruction_string_push(self, instruction: Instruction) -> None:
        assert isinstance(instruction, StringPush)
        self.push(instruction.value)
        self.advance_instruction_pointer()

    def instruction_substring(self, instruction: Instruction) -> None:
        assert isinstance(instruction, SubString)
        end: int = self.pop(int)  # type: ignore
        start: int = self.pop(int)  # type: ignore
        string: str = self.pop(str)  # type: ignore

        if start >= end or start > len(string):
            self.push("")
        else:
            self.push(string[start:end])

        self.advance_instruction_pointer()

    def instruction_string_length(self, instruction: Instruction) -> None:
        assert isinstance(instruction, StringLength)
        x = self.pop(str)
        self.push(len(x))  # type: ignore
        self.advance_instruction_pointer()

    def instruction_call_function(self, instruction: Instruction) -> None:
        assert isinstance(instruction, CallFunction)
        self.call_function(instruction.func_name)

    def instruction_push_function_argument(self, instruction: Instruction) -> None:
        assert isinstance(instruction, PushFunctionArgument)

        arg_value = self.get_function_argument(instruction.arg_name)
        self.push(arg_value)

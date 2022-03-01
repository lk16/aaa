import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple, Type, Union

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
    Equals,
    Instruction,
    IntGreaterEquals,
    IntGreaterThan,
    IntLessEquals,
    IntLessThan,
    IntNotEqual,
    IntPush,
    Jump,
    JumpIf,
    JumpIfNot,
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

        self.instruction_funcs: Dict[
            Type[Instruction], Callable[[Instruction], None]
        ] = {
            And: self.instruction_and,
            BoolPush: self.instruction_boolPush,
            CallFunction: self.instruction_call_function,
            CharNewLinePrint: self.instruction_char_newline_print,
            Divide: self.instruction_divide,
            Drop: self.instruction_drop,
            Dup: self.instruction_dup,
            Equals: self.instruction_equals,
            IntGreaterEquals: self.instruction_int_greater_equals,
            IntGreaterThan: self.instruction_int_greater_than,
            IntLessEquals: self.instruction_int_less_equals,
            IntLessThan: self.instruction_int_less_than,
            IntNotEqual: self.instruction_int_not_equal,
            IntPush: self.instruction_int_push,
            Jump: self.instruction_jump,
            JumpIf: self.instruction_jump_if,
            JumpIfNot: self.instruction_jump_if_not,
            Minus: self.instruction_minus,
            Modulo: self.instruction_modulo,
            Multiply: self.instruction_multiply,
            Not: self.instruction_not,
            Or: self.instruction_or,
            Over: self.instruction_over,
            Plus: self.instruction_plus,
            Print: self.instruction_print,
            PushFunctionArgument: self.instruction_push_function_argument,
            Rot: self.instruction_rot,
            StringLength: self.instruction_string_length,
            StringPush: self.instruction_string_push,
            SubString: self.instruction_substring,
            Swap: self.instruction_swap,
        }

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

    def current_function(self) -> Function:
        func_name = self.call_stack[-1].func_name
        return self.functions[func_name]

    def format_stack_item(self, item: StackItem) -> str:  # pragma: nocover
        if isinstance(item, bool):
            if item:
                return "true"
            return "false"

        if isinstance(item, int):
            return str(item)

        if isinstance(item, str):
            item = item.replace("\n", "\\n").replace('"', '\\"')
            return f'"{item}"'

        raise NotADirectoryError

    def format_str(
        self, string: str, max_length: Optional[int] = None
    ) -> str:  # pragma: nocover
        string = string.replace("\n", "\\n")

        if max_length is not None and len(string) > max_length:
            string = string[: max_length - 1] + "…"

        return string

    def print_debug_info(self) -> None:  # pragma: nocover
        if not self.verbose:
            return

        ip = self.get_instruction_pointer()
        func = self.current_function()
        instructions = get_instructions(func)

        try:
            instruction = instructions[ip].__repr__()
        except IndexError:
            instruction = "<returning>"

        # prevent breaking layout

        instruction = self.format_str(instruction, max_length=30)
        func_name = self.format_str(func.name, max_length=15)

        stack_str = " ".join(self.format_stack_item(item) for item in self.stack)
        stack_str = self.format_str(stack_str, max_length=60)

        print(
            f"DEBUG | {func_name:>15} | IP: {ip:>3} | {instruction:>30} | Stack: {stack_str}",
            file=sys.stderr,
        )

    def print_all_function_instructions(self) -> None:  # pragma: nocover
        # TODO Add function that calls this. This is currently unused.

        if not self.verbose:  # pragma: nocover
            return

        for func in self.functions.values():
            instructions = get_instructions(func)

            func_name = self.format_str(func.name, max_length=15)

            for ip, instr in enumerate(instructions):

                instruction = self.format_str(instr.__repr__(), max_length=30)

                print(
                    f"DEBUG | {func_name:>15} | IP: {ip:>3} | {instruction:>30}",
                    file=sys.stderr,
                )

            print(file=sys.stderr)

        print("---\n", file=sys.stderr)

    def run(self) -> None:
        if self.verbose:  # pragma: nocover
            self.print_all_function_instructions()

        self.call_function("main")

        if self.stack:
            raise StackNotEmptyAtExit

    def call_function(self, func_name: str) -> None:
        # TODO deal with KeyError here
        function = self.functions[func_name]

        argument_values: Dict[str, StackItem] = {
            arg_name: self.pop_untyped() for arg_name in reversed(function.arguments)
        }

        self.call_stack.append(CallStackItem(func_name, 0, argument_values))

        instructions = get_instructions(function)

        while True:
            self.print_debug_info()
            instruction_pointer = self.get_instruction_pointer()

            try:
                instruction = instructions[instruction_pointer]
            except IndexError:
                # We hit the end of the function
                break

            # Excecute the instruction
            try:
                instrunction_func = self.instruction_funcs[type(instruction)]
            except KeyError as e:
                # TODO write test that counts items in self.instruction_funcs
                # so we don't need this check here
                raise UnhandledInstructionError(instruction) from e

            # TODO make instruction_func return instruction pointer
            # so we can debug print the instruction we just executed along with the updated stack on the same line
            # update instruction pointer in self after the debug print
            instrunction_func(instruction)

        self.call_stack.pop()

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
        self.advance_instruction_pointer()
        self.call_function(instruction.func_name)

    def instruction_push_function_argument(self, instruction: Instruction) -> None:
        assert isinstance(instruction, PushFunctionArgument)

        arg_value = self.get_function_argument(instruction.arg_name)
        self.push(arg_value)
        self.advance_instruction_pointer()

    def instruction_jump_if(self, instruction: Instruction) -> None:
        assert isinstance(instruction, JumpIf)

        x = self.pop(bool)

        if x:
            self.jump(instruction.instruction_offset)
        else:
            self.advance_instruction_pointer()

    def instruction_jump_if_not(self, instruction: Instruction) -> None:
        assert isinstance(instruction, JumpIfNot)

        x = self.pop(bool)
        if x:
            self.advance_instruction_pointer()
        else:
            self.jump(instruction.instruction_offset)

    def instruction_jump(self, instruction: Instruction) -> None:
        assert isinstance(instruction, Jump)

        self.jump(instruction.instruction_offset)

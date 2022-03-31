import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Type

from lang.instructions.generator import get_instructions
from lang.instructions.types import (
    And,
    Assert,
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
    JumpIfNot,
    Minus,
    Modulo,
    Multiply,
    Nop,
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
from lang.runtime.program import Program
from lang.typing.signatures import StackItem


@dataclass
class CallStackItem:
    func_name: str
    instruction_pointer: int
    argument_values: Dict[str, StackItem]


class Simulator:
    def __init__(self, program: Program, verbose: bool = False) -> None:
        self.program = program
        self.stack: List[StackItem] = []
        self.call_stack: List[CallStackItem] = []
        self.verbose = verbose

        self.instruction_funcs: Dict[
            Type[Instruction], Callable[[Instruction], int]
        ] = {
            And: self.instruction_and,
            Assert: self.instruction_assert,
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
            JumpIfNot: self.instruction_jump_if_not,
            Minus: self.instruction_minus,
            Modulo: self.instruction_modulo,
            Multiply: self.instruction_multiply,
            Not: self.instruction_not,
            Nop: self.instruction_nop,
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

    def top(self) -> StackItem:
        return self.stack[-1]

    def push(self, item: StackItem) -> None:
        self.stack.append(item)

    def pop(self) -> StackItem:
        return self.stack.pop()

    def get_function_argument(self, arg_name: str) -> StackItem:
        return self.call_stack[-1].argument_values[arg_name]

    def get_instruction_pointer(self) -> int:
        return self.call_stack[-1].instruction_pointer

    def set_instruction_pointer(self, offset: int) -> None:
        self.call_stack[-1].instruction_pointer = offset

    def run(self) -> None:
        self.call_function("main")

    def call_function(self, func_name: str) -> None:
        function = self.program.get_function(func_name)

        assert function  # If this assertion breaks, then Aaa's type checking is broken

        argument_values: Dict[str, StackItem] = {
            arg.name: self.pop() for arg in reversed(function.arguments)
        }

        self.call_stack.append(CallStackItem(func_name, 0, argument_values))

        instructions = get_instructions(function)

        while True:
            instruction_pointer = self.get_instruction_pointer()

            try:
                instruction = instructions[instruction_pointer]
            except IndexError:
                # We hit the end of the function
                break

            # Excecute the instruction and get value for next instruction ointer
            next_instruction = self.instruction_funcs[type(instruction)](instruction)
            self.set_instruction_pointer(next_instruction)

        self.call_stack.pop()

    def instruction_int_push(self, instruction: Instruction) -> int:
        assert isinstance(instruction, IntPush)
        self.push(instruction.value)
        return self.get_instruction_pointer() + 1

    def instruction_plus(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Plus)
        x: int | str = self.pop()
        y: int | str = self.pop()

        self.push(y + x)  # type: ignore
        return self.get_instruction_pointer() + 1

    def instruction_minus(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Minus)
        x: int = self.pop()  # type: ignore
        y: int = self.pop()  # type: ignore
        self.push(y - x)
        return self.get_instruction_pointer() + 1

    def instruction_multiply(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Multiply)
        x: int = self.pop()  # type: ignore
        y: int = self.pop()  # type: ignore
        self.push(x * y)
        return self.get_instruction_pointer() + 1

    def instruction_divide(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Divide)
        x: int = self.pop()  # type: ignore
        y: int = self.pop()  # type: ignore
        self.push(y // x)
        return self.get_instruction_pointer() + 1

    def instruction_modulo(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Modulo)
        x: int = self.pop()  # type: ignore
        y: int = self.pop()  # type: ignore
        self.push(y % x)
        return self.get_instruction_pointer() + 1

    def instruction_boolPush(self, instruction: Instruction) -> int:
        assert isinstance(instruction, BoolPush)
        self.push(instruction.value)
        return self.get_instruction_pointer() + 1

    def instruction_and(self, instruction: Instruction) -> int:
        assert isinstance(instruction, And)
        x: bool = self.pop()  # type: ignore
        y: bool = self.pop()  # type: ignore
        self.push(x and y)
        return self.get_instruction_pointer() + 1

    def instruction_or(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Or)
        x: bool = self.pop()  # type: ignore
        y: bool = self.pop()  # type: ignore
        self.push(x or y)
        return self.get_instruction_pointer() + 1

    def instruction_not(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Not)
        x: bool = self.pop()  # type: ignore
        self.push(not x)
        return self.get_instruction_pointer() + 1

    def instruction_equals(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Equals)
        x = self.pop()
        y = self.pop()
        self.push(x == y)
        return self.get_instruction_pointer() + 1

    def instruction_int_less_than(self, instruction: Instruction) -> int:
        assert isinstance(instruction, IntLessThan)
        x: int = self.pop()  # type: ignore
        y: int = self.pop()  # type: ignore
        self.push(y < x)
        return self.get_instruction_pointer() + 1

    def instruction_int_less_equals(self, instruction: Instruction) -> int:
        assert isinstance(instruction, IntLessEquals)
        x: int = self.pop()  # type: ignore
        y: int = self.pop()  # type: ignore
        self.push(y <= x)
        return self.get_instruction_pointer() + 1

    def instruction_int_greater_than(self, instruction: Instruction) -> int:
        assert isinstance(instruction, IntGreaterThan)
        x: int = self.pop()  # type: ignore
        y: int = self.pop()  # type: ignore
        self.push(y > x)
        return self.get_instruction_pointer() + 1

    def instruction_int_greater_equals(self, instruction: Instruction) -> int:
        assert isinstance(instruction, IntGreaterEquals)
        x: int = self.pop()  # type: ignore
        y: int = self.pop()  # type: ignore
        self.push(y >= x)
        return self.get_instruction_pointer() + 1

    def instruction_int_not_equal(self, instruction: Instruction) -> int:
        assert isinstance(instruction, IntNotEqual)
        x = self.pop()
        y = self.pop()
        self.push(y != x)
        return self.get_instruction_pointer() + 1

    def instruction_drop(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Drop)
        self.pop()
        return self.get_instruction_pointer() + 1

    def instruction_dup(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Dup)
        x = self.top()
        self.push(x)
        return self.get_instruction_pointer() + 1

    def instruction_swap(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Swap)
        x = self.pop()
        y = self.pop()
        self.push(x)
        self.push(y)
        return self.get_instruction_pointer() + 1

    def instruction_over(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Over)
        x = self.pop()
        y = self.top()
        self.push(x)
        self.push(y)
        return self.get_instruction_pointer() + 1

    def instruction_rot(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Rot)
        x = self.pop()
        y = self.pop()
        z = self.pop()
        self.push(y)
        self.push(x)
        self.push(z)
        return self.get_instruction_pointer() + 1

    def instruction_char_newline_print(self, instruction: Instruction) -> int:
        assert isinstance(instruction, CharNewLinePrint)
        print()  # Just print a newline
        return self.get_instruction_pointer() + 1

    def instruction_print(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Print)
        x = self.pop()
        if type(x) == bool:
            if x:
                print("true", end="")
            else:
                print("false", end="")
        else:
            print(x, end="")

        return self.get_instruction_pointer() + 1

    def instruction_string_push(self, instruction: Instruction) -> int:
        assert isinstance(instruction, StringPush)
        self.push(instruction.value)
        return self.get_instruction_pointer() + 1

    def instruction_substring(self, instruction: Instruction) -> int:
        assert isinstance(instruction, SubString)
        end: int = self.pop()  # type: ignore
        start: int = self.pop()  # type: ignore
        string: str = self.pop()  # type: ignore

        if start >= end or start > len(string):
            self.push("")
        else:
            self.push(string[start:end])

        return self.get_instruction_pointer() + 1

    def instruction_string_length(self, instruction: Instruction) -> int:
        assert isinstance(instruction, StringLength)
        x: str = self.pop()  # type: ignore
        self.push(len(x))
        return self.get_instruction_pointer() + 1

    def instruction_call_function(self, instruction: Instruction) -> int:
        assert isinstance(instruction, CallFunction)
        self.call_function(instruction.func_name)
        return self.get_instruction_pointer() + 1

    def instruction_push_function_argument(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushFunctionArgument)

        arg_value = self.get_function_argument(instruction.arg_name)
        self.push(arg_value)
        return self.get_instruction_pointer() + 1

    def instruction_jump_if_not(self, instruction: Instruction) -> int:
        assert isinstance(instruction, JumpIfNot)

        x: bool = self.pop()  # type: ignore
        if x:
            return self.get_instruction_pointer() + 1
        else:
            return instruction.instruction_offset

    def instruction_jump(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Jump)
        return instruction.instruction_offset

    def instruction_nop(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Nop)
        return self.get_instruction_pointer() + 1

    def instruction_assert(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Assert)
        x: bool = self.pop()  # type: ignore

        if not x:
            print("Assertion failure", file=sys.stderr)
            # TODO print Aaa stack trace
            exit(1)

        return self.get_instruction_pointer() + 1

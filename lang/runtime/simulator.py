import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Type

from lang.instructions.types import (
    And,
    Assert,
    CallFunction,
    Divide,
    Drop,
    Dup,
    Equals,
    GetStructField,
    Instruction,
    IntGreaterEquals,
    IntGreaterThan,
    IntLessEquals,
    IntLessThan,
    IntNotEqual,
    Jump,
    JumpIfNot,
    MapClear,
    MapCopy,
    MapDrop,
    MapEmpty,
    MapGet,
    MapHasKey,
    MapKeys,
    MapPop,
    MapSet,
    MapSize,
    MapValues,
    Minus,
    Modulo,
    Multiply,
    Nop,
    Not,
    Or,
    Over,
    Plus,
    Print,
    PushBool,
    PushFunctionArgument,
    PushInt,
    PushMap,
    PushString,
    PushStruct,
    PushVec,
    Rot,
    SetStructField,
    StringLength,
    SubString,
    Swap,
    VecClear,
    VecCopy,
    VecEmpty,
    VecGet,
    VecPop,
    VecPush,
    VecSet,
    VecSize,
)
from lang.runtime.debug import format_str
from lang.runtime.parse import Function, TypeLiteral
from lang.runtime.program import Program
from lang.typing.types import (
    RootType,
    Variable,
    VariableType,
    bool_var,
    int_var,
    str_var,
)


@dataclass
class CallStackItem:
    func_name: str
    source_file: Path
    instruction_pointer: int
    argument_values: Dict[str, Variable]


class Simulator:
    def __init__(self, program: Program, verbose: bool = False) -> None:
        self.program = program
        self.stack: List[Variable] = []
        self.call_stack: List[CallStackItem] = []
        self.verbose = verbose

        self.instruction_funcs: Dict[
            Type[Instruction], Callable[[Instruction], int]
        ] = {
            And: self.instruction_and,
            Assert: self.instruction_assert,
            CallFunction: self.instruction_call_function,
            Divide: self.instruction_divide,
            Drop: self.instruction_drop,
            Dup: self.instruction_dup,
            Equals: self.instruction_equals,
            IntGreaterEquals: self.instruction_int_greater_equals,
            IntGreaterThan: self.instruction_int_greater_than,
            IntLessEquals: self.instruction_int_less_equals,
            IntLessThan: self.instruction_int_less_than,
            IntNotEqual: self.instruction_int_not_equal,
            Jump: self.instruction_jump,
            JumpIfNot: self.instruction_jump_if_not,
            Minus: self.instruction_minus,
            Modulo: self.instruction_modulo,
            Multiply: self.instruction_multiply,
            Nop: self.instruction_nop,
            Not: self.instruction_not,
            Or: self.instruction_or,
            Over: self.instruction_over,
            Plus: self.instruction_plus,
            Print: self.instruction_print,
            PushBool: self.instruction_push_bool,
            PushFunctionArgument: self.instruction_push_function_argument,
            PushInt: self.instruction_push_int,
            PushMap: self.instruction_map_push,
            PushString: self.instruction_push_string,
            PushStruct: self.instruction_push_struct,
            PushVec: self.instruction_push_vec,
            Rot: self.instruction_rot,
            StringLength: self.instruction_string_length,
            SubString: self.instruction_substring,
            Swap: self.instruction_swap,
            VecPush: self.instruction_vec_push,
            VecPop: self.instruction_vec_pop,
            VecSet: self.instruction_vec_set,
            VecGet: self.instruction_vec_get,
            VecSize: self.instruction_vec_size,
            VecEmpty: self.instruction_vec_empty,
            VecClear: self.instruction_vec_clear,
            VecCopy: self.instruction_vec_copy,
            MapGet: self.instruction_map_get,
            MapSet: self.instruction_map_set,
            MapHasKey: self.instruction_map_has_key,
            MapSize: self.instruction_map_size,
            MapEmpty: self.instruction_map_empty,
            MapPop: self.instruction_map_pop,
            MapDrop: self.instruction_map_drop,
            MapClear: self.instruction_map_clear,
            MapCopy: self.instruction_map_copy,
            MapKeys: self.instruction_map_keys,
            MapValues: self.instruction_map_values,
            GetStructField: self.instruction_get_struct_field,
            SetStructField: self.instruction_set_struct_field,
        }

    def top(self) -> Variable:
        return self.stack[-1]

    def push(self, item: Variable) -> None:
        self.stack.append(item)

    def pop(self) -> Variable:
        return self.stack.pop()

    def get_function_argument(self, arg_name: str) -> Variable:
        return self.call_stack[-1].argument_values[arg_name]

    def get_instruction_pointer(self) -> int:
        return self.call_stack[-1].instruction_pointer

    def set_instruction_pointer(self, offset: int) -> None:
        self.call_stack[-1].instruction_pointer = offset

    def print_debug_info(self) -> None:  # pragma: nocover
        if not self.verbose:
            return

        ip = self.get_instruction_pointer()
        current_function = self.call_stack[-1]
        func_name = current_function.func_name
        instructions = self.program.get_instructions(
            file=current_function.source_file, name=func_name
        )

        try:
            instruction = instructions[ip].__repr__()
        except IndexError:
            instruction = "<returning>"

        # prevent breaking layout

        instruction = format_str(instruction, max_length=30)
        func_name = format_str(func_name, max_length=15)

        stack_str = " ".join(repr(item) for item in self.stack)
        stack_str = format_str(stack_str, max_length=60)

        print(
            f"DEBUG | {func_name:>15} | IP: {ip:>3} | {instruction:>30} | Stack: {stack_str}",
            file=sys.stderr,
        )

    def run(self) -> None:
        if self.verbose:  # pragma: nocover
            self.program.print_all_instructions()

        self.call_function(self.program.entry_point_file, "main")

    def call_function(self, file: Path, func_name: str) -> None:
        function = self.program.get_identifier(file, func_name)

        # If this assertion breaks, then Aaa's type checking is broken
        assert isinstance(function, Function)

        argument_values: Dict[str, Variable] = {}

        for argument in reversed(function.arguments):
            argument_values[argument.name] = self.pop()

        self.call_stack.append(
            CallStackItem(
                func_name=func_name,
                source_file=file,
                instruction_pointer=0,
                argument_values=argument_values,
            )
        )

        instructions = self.program.get_instructions(file, function.name_key())

        while True:
            instruction_pointer = self.get_instruction_pointer()

            try:
                instruction = instructions[instruction_pointer]
            except IndexError:
                # We hit the end of the function
                break

            # Excecute the instruction and get value for next instruction ointer
            next_instruction = self.instruction_funcs[type(instruction)](instruction)
            self.print_debug_info()
            self.set_instruction_pointer(next_instruction)

        self.call_stack.pop()

    def instruction_push_int(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushInt)
        self.push(int_var(instruction.value))
        return self.get_instruction_pointer() + 1

    def instruction_plus(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Plus)
        x: int | str = self.pop().value
        y: int | str = self.pop().value

        # TODO make different instruction for string concatenation

        if type(x) is int:
            total = int_var(y + x)  # type: ignore
        else:
            total = str_var(y + x)  # type: ignore

        self.push(total)
        return self.get_instruction_pointer() + 1

    def instruction_minus(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Minus)
        x: int = self.pop().value
        y: int = self.pop().value
        self.push(int_var(y - x))
        return self.get_instruction_pointer() + 1

    def instruction_multiply(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Multiply)
        x: int = self.pop().value
        y: int = self.pop().value
        self.push(int_var(x * y))
        return self.get_instruction_pointer() + 1

    def instruction_divide(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Divide)
        x: int = self.pop().value
        y: int = self.pop().value
        self.push(int_var(y // x))
        return self.get_instruction_pointer() + 1

    def instruction_modulo(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Modulo)
        x: int = self.pop().value
        y: int = self.pop().value
        self.push(int_var(y % x))
        return self.get_instruction_pointer() + 1

    def instruction_push_bool(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushBool)
        self.push(bool_var(instruction.value))
        return self.get_instruction_pointer() + 1

    def instruction_and(self, instruction: Instruction) -> int:
        assert isinstance(instruction, And)
        x: bool = self.pop().value
        y: bool = self.pop().value
        self.push(bool_var(x and y))
        return self.get_instruction_pointer() + 1

    def instruction_or(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Or)
        x: bool = self.pop().value
        y: bool = self.pop().value
        self.push(bool_var(x or y))
        return self.get_instruction_pointer() + 1

    def instruction_not(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Not)
        x: bool = self.pop().value
        self.push(bool_var(not x))
        return self.get_instruction_pointer() + 1

    def instruction_equals(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Equals)
        x = self.pop().value
        y = self.pop().value
        self.push(bool_var(x == y))
        return self.get_instruction_pointer() + 1

    def instruction_int_less_than(self, instruction: Instruction) -> int:
        assert isinstance(instruction, IntLessThan)
        x: int = self.pop().value
        y: int = self.pop().value
        self.push(bool_var(y < x))
        return self.get_instruction_pointer() + 1

    def instruction_int_less_equals(self, instruction: Instruction) -> int:
        assert isinstance(instruction, IntLessEquals)
        x: int = self.pop().value
        y: int = self.pop().value
        self.push(bool_var(y <= x))
        return self.get_instruction_pointer() + 1

    def instruction_int_greater_than(self, instruction: Instruction) -> int:
        assert isinstance(instruction, IntGreaterThan)
        x: int = self.pop().value
        y: int = self.pop().value
        self.push(bool_var(y > x))
        return self.get_instruction_pointer() + 1

    def instruction_int_greater_equals(self, instruction: Instruction) -> int:
        assert isinstance(instruction, IntGreaterEquals)
        x: int = self.pop().value
        y: int = self.pop().value
        self.push(bool_var(y >= x))
        return self.get_instruction_pointer() + 1

    def instruction_int_not_equal(self, instruction: Instruction) -> int:
        assert isinstance(instruction, IntNotEqual)
        x = self.pop().value
        y = self.pop().value
        self.push(bool_var(y != x))
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

    def instruction_print(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Print)
        x_var = self.pop()
        print(x_var, end="")
        return self.get_instruction_pointer() + 1

    def instruction_push_string(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushString)
        self.push(str_var(instruction.value))
        return self.get_instruction_pointer() + 1

    def instruction_substring(self, instruction: Instruction) -> int:
        assert isinstance(instruction, SubString)
        end: int = self.pop().value
        start: int = self.pop().value
        string: str = self.pop().value

        if start >= end or start > len(string):
            result_str = ""
        else:
            result_str = string[start:end]

        self.push(str_var(result_str))
        return self.get_instruction_pointer() + 1

    def instruction_string_length(self, instruction: Instruction) -> int:
        assert isinstance(instruction, StringLength)
        x: str = self.pop().value
        self.push(int_var(len(x)))
        return self.get_instruction_pointer() + 1

    def instruction_call_function(self, instruction: Instruction) -> int:
        assert isinstance(instruction, CallFunction)
        self.call_function(instruction.file, instruction.func_name)
        return self.get_instruction_pointer() + 1

    def instruction_push_function_argument(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushFunctionArgument)

        arg_value = self.get_function_argument(instruction.arg_name)
        self.push(arg_value)
        return self.get_instruction_pointer() + 1

    def instruction_jump_if_not(self, instruction: Instruction) -> int:
        assert isinstance(instruction, JumpIfNot)

        x: bool = self.pop().value
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
        x: bool = self.pop().value

        if not x:
            print("Assertion failure, stacktrace:", file=sys.stderr)
            for call_stack_item in self.call_stack:
                name = call_stack_item.func_name

                args = ""
                if call_stack_item.argument_values:  # pragma: nocover
                    args = ", arguments: " + ", ".join(
                        f"{name}={value.__repr__()}"
                        for name, value in call_stack_item.argument_values.items()
                    )

                print(f"- {name}{args}", file=sys.stderr)

            # TODO add filename and line number to stacktrace
            exit(1)

        return self.get_instruction_pointer() + 1

    def instruction_map_push(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushMap)
        map_var = Variable(
            RootType.MAPPING,
            {},
            type_params=[instruction.key_type, instruction.value_type],
        )
        self.push(map_var)
        return self.get_instruction_pointer() + 1

    def instruction_push_vec(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushVec)
        map_var = Variable(
            RootType.VECTOR,
            [],
            type_params=[instruction.item_type],
        )
        self.push(map_var)
        return self.get_instruction_pointer() + 1

    def instruction_vec_push(self, instruction: Instruction) -> int:
        assert isinstance(instruction, VecPush)
        x = self.pop()
        vec: List[Variable] = self.top().value

        vec.append(x)
        return self.get_instruction_pointer() + 1

    def instruction_vec_pop(self, instruction: Instruction) -> int:
        assert isinstance(instruction, VecPop)
        vec: List[Variable] = self.top().value

        x = vec.pop()
        self.push(x)

        return self.get_instruction_pointer() + 1

    def instruction_vec_get(self, instruction: Instruction) -> int:
        assert isinstance(instruction, VecGet)
        x: int = self.pop().value
        vec: List[Variable] = self.top().value

        self.push(vec[x])
        return self.get_instruction_pointer() + 1

    def instruction_vec_set(self, instruction: Instruction) -> int:
        assert isinstance(instruction, VecSet)
        x: Any = self.pop()
        index: int = self.pop().value
        vec: List[Variable] = self.top().value

        vec[index] = x
        return self.get_instruction_pointer() + 1

    def instruction_vec_size(self, instruction: Instruction) -> int:
        assert isinstance(instruction, VecSize)
        vec: List[Variable] = self.top().value

        self.push(int_var(len(vec)))
        return self.get_instruction_pointer() + 1

    def instruction_vec_empty(self, instruction: Instruction) -> int:
        assert isinstance(instruction, VecEmpty)
        vec: List[Variable] = self.top().value

        self.push(bool_var(not bool(vec)))
        return self.get_instruction_pointer() + 1

    def instruction_vec_clear(self, instruction: Instruction) -> int:
        assert isinstance(instruction, VecClear)
        vec: List[Variable] = self.top().value

        vec.clear()
        return self.get_instruction_pointer() + 1

    def instruction_vec_copy(self, instruction: Instruction) -> int:
        assert isinstance(instruction, VecCopy)
        vec_var = self.top()

        copied = Variable(
            vec_var.root_type(),
            deepcopy(vec_var.value),
            deepcopy(vec_var.type.type_params),
        )

        self.push(copied)
        return self.get_instruction_pointer() + 1

    def instruction_map_get(self, instruction: Instruction) -> int:
        assert isinstance(instruction, MapGet)
        key = self.pop()
        map: Dict[Variable, Variable] = self.top().value

        self.push(map[key])
        return self.get_instruction_pointer() + 1

    def instruction_map_set(self, instruction: Instruction) -> int:
        assert isinstance(instruction, MapSet)
        value = self.pop()
        key = self.pop()
        map: Dict[Variable, Variable] = self.top().value

        map[key] = value
        return self.get_instruction_pointer() + 1

    def instruction_map_has_key(self, instruction: Instruction) -> int:
        assert isinstance(instruction, MapHasKey)
        key = self.pop()
        map: Dict[Variable, Variable] = self.top().value

        self.push(bool_var(key in map))
        return self.get_instruction_pointer() + 1

    def instruction_map_size(self, instruction: Instruction) -> int:
        assert isinstance(instruction, MapSize)
        map: Dict[Variable, Variable] = self.top().value

        self.push(int_var(len(map)))
        return self.get_instruction_pointer() + 1

    def instruction_map_empty(self, instruction: Instruction) -> int:
        assert isinstance(instruction, MapEmpty)
        map: Dict[Variable, Variable] = self.top().value

        self.push(bool_var(not bool(map)))
        return self.get_instruction_pointer() + 1

    def instruction_map_pop(self, instruction: Instruction) -> int:
        assert isinstance(instruction, MapPop)
        key = self.pop()
        map: Dict[Variable, Variable] = self.top().value

        self.push(map.pop(key))
        return self.get_instruction_pointer() + 1

    def instruction_map_drop(self, instruction: Instruction) -> int:
        assert isinstance(instruction, MapDrop)
        key = self.pop()
        map: Dict[Variable, Variable] = self.top().value

        del map[key]
        return self.get_instruction_pointer() + 1

    def instruction_map_clear(self, instruction: Instruction) -> int:
        assert isinstance(instruction, MapClear)
        map: Dict[Variable, Variable] = self.top().value

        map.clear()
        return self.get_instruction_pointer() + 1

    def instruction_map_copy(self, instruction: Instruction) -> int:
        assert isinstance(instruction, MapCopy)
        map_var = self.top()

        copied = Variable(
            map_var.root_type(),
            deepcopy(map_var.value),
            deepcopy(map_var.type.type_params),
        )

        self.push(copied)
        return self.get_instruction_pointer() + 1

    def instruction_map_keys(self, instruction: Instruction) -> int:
        raise NotImplementedError

    def instruction_map_values(self, instruction: Instruction) -> int:
        raise NotImplementedError

    def instruction_push_struct(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushStruct)

        struct_fields: Dict[str, Variable] = {}

        for field in instruction.type.fields:
            assert isinstance(field.type.type, TypeLiteral)
            var_type = VariableType.from_type_literal(field.type.type)
            struct_fields[field.name] = Variable.zero_value(var_type)

        struct_var = Variable(
            RootType.STRUCT, struct_fields, struct_name=instruction.type.name
        )
        self.push(struct_var)

        return self.get_instruction_pointer() + 1

    def instruction_get_struct_field(self, instruction: Instruction) -> int:
        assert isinstance(instruction, GetStructField)

        field_name: str = self.pop().value
        struct_fields: Dict[str, Variable] = self.top().value
        self.push(struct_fields[field_name])

        return self.get_instruction_pointer() + 1

    def instruction_set_struct_field(self, instruction: Instruction) -> int:
        assert isinstance(instruction, SetStructField)

        new_value: Variable = self.pop()
        field_name: str = self.pop().value
        struct_fields: Dict[str, Variable] = self.top().value
        struct_fields[field_name] = new_value

        return self.get_instruction_pointer() + 1

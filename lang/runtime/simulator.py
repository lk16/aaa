import os
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, List, Type

from lang.exceptions import AaaRuntimeException
from lang.exceptions.runtime import AaaAssertionFailure
from lang.models.instructions import (
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
    StandardLibraryCall,
    StandardLibraryCallKind,
    Swap,
)
from lang.models.parse import Function
from lang.models.runtime import CallStackItem
from lang.models.typing.var import (
    Variable,
    bool_var,
    int_var,
    map_var,
    str_var,
    vec_var,
)
from lang.models.typing.var_type import RootType, Str, VariableType
from lang.runtime.debug import format_str
from lang.runtime.program import Program


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
            Swap: self.instruction_swap,
            StandardLibraryCall: self.instruction_stdandard_library_call,
            GetStructField: self.instruction_get_struct_field,
            SetStructField: self.instruction_set_struct_field,
        }

        self.stdlib_funcs: Dict[StandardLibraryCallKind, Callable[[], int]] = {
            StandardLibraryCallKind.ENVIRON: self.instruction_environ,
            StandardLibraryCallKind.GETENV: self.instruction_getenv,
            StandardLibraryCallKind.MAP_CLEAR: self.instruction_map_clear,
            StandardLibraryCallKind.MAP_COPY: self.instruction_map_copy,
            StandardLibraryCallKind.MAP_DROP: self.instruction_map_drop,
            StandardLibraryCallKind.MAP_EMPTY: self.instruction_map_empty,
            StandardLibraryCallKind.MAP_GET: self.instruction_map_get,
            StandardLibraryCallKind.MAP_HAS_KEY: self.instruction_map_has_key,
            StandardLibraryCallKind.MAP_KEYS: self.instruction_map_keys,
            StandardLibraryCallKind.MAP_POP: self.instruction_map_pop,
            StandardLibraryCallKind.MAP_SET: self.instruction_map_set,
            StandardLibraryCallKind.MAP_SIZE: self.instruction_map_size,
            StandardLibraryCallKind.MAP_VALUES: self.instruction_map_values,
            StandardLibraryCallKind.SETENV: self.instruction_setenv,
            StandardLibraryCallKind.STR_APPEND: self.instruction_str_append,
            StandardLibraryCallKind.STR_CONTAINS: self.instruction_str_contains,
            StandardLibraryCallKind.STR_EQUALS: self.instruction_str_equals,
            StandardLibraryCallKind.STR_FIND: self.instruction_str_find,
            StandardLibraryCallKind.STR_FIND_AFTER: self.instruction_str_find_after,
            StandardLibraryCallKind.STR_JOIN: self.instruction_str_join,
            StandardLibraryCallKind.STR_LEN: self.instruction_str_len,
            StandardLibraryCallKind.STR_LOWER: self.instruction_str_lower,
            StandardLibraryCallKind.STR_REPLACE: self.instruction_str_replace,
            StandardLibraryCallKind.STR_SPLIT: self.instruction_str_split,
            StandardLibraryCallKind.STR_STRIP: self.instruction_str_strip,
            StandardLibraryCallKind.STR_SUBSTR: self.instruction_str_substr,
            StandardLibraryCallKind.STR_TO_BOOL: self.instruction_str_to_bool,
            StandardLibraryCallKind.STR_TO_INT: self.instruction_str_to_int,
            StandardLibraryCallKind.STR_UPPER: self.instruction_str_upper,
            StandardLibraryCallKind.SYSCALL_CHDIR: self.instruction_syscall_chdir,
            StandardLibraryCallKind.SYSCALL_CLOSE: self.instruction_syscall_close,
            StandardLibraryCallKind.SYSCALL_EXECVE: self.instruction_syscall_execve,
            StandardLibraryCallKind.SYSCALL_EXIT: self.instruction_syscall_exit,
            StandardLibraryCallKind.SYSCALL_FORK: self.instruction_syscall_fork,
            StandardLibraryCallKind.SYSCALL_FSYNC: self.instruction_syscall_fsync,
            StandardLibraryCallKind.SYSCALL_GETCWD: self.instruction_syscall_getcwd,
            StandardLibraryCallKind.SYSCALL_GETPID: self.instruction_getpid,
            StandardLibraryCallKind.SYSCALL_GETPPID: self.instruction_getppid,
            StandardLibraryCallKind.SYSCALL_OPEN: self.instruction_open,
            StandardLibraryCallKind.SYSCALL_READ: self.instruction_syscall_read,
            StandardLibraryCallKind.SYSCALL_TIME: self.instruction_syscall_time,
            StandardLibraryCallKind.SYSCALL_WAITPID: self.instruction_waitpid,
            StandardLibraryCallKind.SYSCALL_WRITE: self.instruction_write,
            StandardLibraryCallKind.UNSETENV: self.instruction_unsetenv,
            StandardLibraryCallKind.VEC_CLEAR: self.instruction_vec_clear,
            StandardLibraryCallKind.VEC_COPY: self.instruction_vec_copy,
            StandardLibraryCallKind.VEC_EMPTY: self.instruction_vec_empty,
            StandardLibraryCallKind.VEC_GET: self.instruction_vec_get,
            StandardLibraryCallKind.VEC_POP: self.instruction_vec_pop,
            StandardLibraryCallKind.VEC_PUSH: self.instruction_vec_push,
            StandardLibraryCallKind.VEC_SET: self.instruction_vec_set,
            StandardLibraryCallKind.VEC_SIZE: self.instruction_vec_size,
        }

    def top(self) -> Variable:
        return self.stack[-1]

    def push_var(self, item: Variable) -> None:
        self.stack.append(item)

    def push_int(self, item: int) -> None:
        self.push_var(int_var(item))

    def push_str(self, item: str) -> None:
        self.push_var(str_var(item))

    def push_bool(self, item: bool) -> None:
        self.push_var(bool_var(item))

    def pop_var(self) -> Variable:
        return self.stack.pop()

    def pop_int(self) -> int:
        popped = self.stack.pop().value
        assert isinstance(popped, int)
        return popped

    def pop_str(self) -> str:
        popped = self.stack.pop().value
        assert isinstance(popped, str)
        return popped

    def pop_bool(self) -> bool:
        popped = self.stack.pop().value
        assert isinstance(popped, bool)
        return popped

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
        call_stack_item = self.call_stack[-1]
        func_name = call_stack_item.function.identify()
        instructions = self.program.get_instructions(
            file=call_stack_item.source_file, name=func_name
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

    def run(self, raise_: bool = False) -> None:
        if self.verbose:  # pragma: nocover
            self.program.print_all_instructions()

        try:
            self.call_function(self.program.entry_point_file, "main")
        except AaaRuntimeException as e:  # pragma: nocover
            print(e, file=sys.stderr)
            if raise_:  # This is for testing. TODO find better solution
                raise e
            else:
                exit(1)

    def call_function(self, file: Path, func_name: str) -> None:
        function = self.program.get_identifier(file, func_name)

        # If this assertion breaks, then Aaa's type checking is broken
        assert isinstance(function, Function)

        argument_values: Dict[str, Variable] = {}

        for argument in reversed(function.arguments):
            argument_values[argument.name] = self.pop_var()

        self.call_stack.append(
            CallStackItem(
                function=function,
                source_file=file,
                instruction_pointer=0,
                argument_values=argument_values,
            )
        )

        instructions = self.program.get_instructions(file, str(function.name))

        while True:
            instruction_pointer = self.get_instruction_pointer()

            try:
                instruction = instructions[instruction_pointer]
            except IndexError:
                # We hit the end of the function
                break

            # Excecute the instruction and get value for next instruction pointer
            next_instruction = self.instruction_funcs[type(instruction)](instruction)
            self.print_debug_info()
            self.set_instruction_pointer(next_instruction)

        self.call_stack.pop()

    def instruction_push_int(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushInt)
        self.push_var(int_var(instruction.value))
        return self.get_instruction_pointer() + 1

    def instruction_plus(self, instruction: Instruction) -> int:
        x = self.pop_int()
        y = self.pop_int()

        self.push_int(y + x)
        return self.get_instruction_pointer() + 1

    def instruction_minus(self, instruction: Instruction) -> int:
        x = self.pop_int()
        y = self.pop_int()

        self.push_int(y - x)
        return self.get_instruction_pointer() + 1

    def instruction_multiply(self, instruction: Instruction) -> int:
        x = self.pop_int()
        y = self.pop_int()

        self.push_int(x * y)
        return self.get_instruction_pointer() + 1

    def instruction_divide(self, instruction: Instruction) -> int:
        x = self.pop_int()
        y = self.pop_int()

        if x == 0:
            self.push_int(0)
            self.push_bool(False)
        else:
            self.push_int(y // x)
            self.push_bool(True)

        return self.get_instruction_pointer() + 1

    def instruction_modulo(self, instruction: Instruction) -> int:
        x = self.pop_int()
        y = self.pop_int()

        if x == 0:
            self.push_int(0)
            self.push_bool(False)
        else:
            self.push_int(y % x)
            self.push_bool(True)

        return self.get_instruction_pointer() + 1

    def instruction_push_bool(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushBool)
        self.push_bool(instruction.value)
        return self.get_instruction_pointer() + 1

    def instruction_and(self, instruction: Instruction) -> int:
        x = self.pop_bool()
        y = self.pop_bool()

        self.push_bool(x and y)
        return self.get_instruction_pointer() + 1

    def instruction_or(self, instruction: Instruction) -> int:
        x = self.pop_bool()
        y = self.pop_bool()
        self.push_bool(x or y)
        return self.get_instruction_pointer() + 1

    def instruction_not(self, instruction: Instruction) -> int:
        x = self.pop_bool()
        self.push_bool(not x)
        return self.get_instruction_pointer() + 1

    def instruction_equals(self, instruction: Instruction) -> int:
        x = self.pop_int()
        y = self.pop_int()
        self.push_bool(x == y)
        return self.get_instruction_pointer() + 1

    def instruction_int_less_than(self, instruction: Instruction) -> int:
        x = self.pop_int()
        y = self.pop_int()
        self.push_bool(y < x)
        return self.get_instruction_pointer() + 1

    def instruction_int_less_equals(self, instruction: Instruction) -> int:
        x = self.pop_int()
        y = self.pop_int()
        self.push_bool(y <= x)
        return self.get_instruction_pointer() + 1

    def instruction_int_greater_than(self, instruction: Instruction) -> int:
        x = self.pop_int()
        y = self.pop_int()
        self.push_bool(y > x)
        return self.get_instruction_pointer() + 1

    def instruction_int_greater_equals(self, instruction: Instruction) -> int:
        x = self.pop_int()
        y = self.pop_int()
        self.push_bool(y >= x)
        return self.get_instruction_pointer() + 1

    def instruction_int_not_equal(self, instruction: Instruction) -> int:
        x = self.pop_int()
        y = self.pop_int()
        self.push_bool(y != x)
        return self.get_instruction_pointer() + 1

    def instruction_drop(self, instruction: Instruction) -> int:
        self.pop_var()
        return self.get_instruction_pointer() + 1

    def instruction_dup(self, instruction: Instruction) -> int:
        x = self.top()
        self.push_var(x)
        return self.get_instruction_pointer() + 1

    def instruction_swap(self, instruction: Instruction) -> int:
        x = self.pop_var()
        y = self.pop_var()
        self.push_var(x)
        self.push_var(y)
        return self.get_instruction_pointer() + 1

    def instruction_over(self, instruction: Instruction) -> int:
        x = self.pop_var()
        y = self.top()
        self.push_var(x)
        self.push_var(y)
        return self.get_instruction_pointer() + 1

    def instruction_rot(self, instruction: Instruction) -> int:
        x = self.pop_var()
        y = self.pop_var()
        z = self.pop_var()
        self.push_var(y)
        self.push_var(x)
        self.push_var(z)
        return self.get_instruction_pointer() + 1

    def instruction_print(self, instruction: Instruction) -> int:
        x_var = self.pop_var()
        print(x_var, end="")
        return self.get_instruction_pointer() + 1

    def instruction_push_string(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushString)
        self.push_str(instruction.value)
        return self.get_instruction_pointer() + 1

    def instruction_call_function(self, instruction: Instruction) -> int:
        assert isinstance(instruction, CallFunction)
        self.call_function(instruction.file, instruction.func_name)
        return self.get_instruction_pointer() + 1

    def instruction_push_function_argument(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushFunctionArgument)

        arg_value = self.get_function_argument(instruction.arg_name)
        self.push_var(arg_value)
        return self.get_instruction_pointer() + 1

    def instruction_jump_if_not(self, instruction: Instruction) -> int:
        assert isinstance(instruction, JumpIfNot)

        x = self.pop_bool()
        if x:
            return self.get_instruction_pointer() + 1
        else:
            return instruction.instruction_offset

    def instruction_jump(self, instruction: Instruction) -> int:
        assert isinstance(instruction, Jump)
        return instruction.instruction_offset

    def instruction_nop(self, instruction: Instruction) -> int:
        return self.get_instruction_pointer() + 1

    def instruction_assert(self, instruction: Instruction) -> int:
        x = self.pop_bool()

        if not x:
            call_stack_copy = deepcopy(self.call_stack)
            raise AaaAssertionFailure(call_stack_copy)

        return self.get_instruction_pointer() + 1

    def instruction_map_push(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushMap)
        map_var = Variable(
            type=VariableType(
                root_type=RootType.MAPPING,
                type_params=[instruction.key_type, instruction.value_type],
            ),
            value={},
        )
        self.push_var(map_var)
        return self.get_instruction_pointer() + 1

    def instruction_push_vec(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushVec)
        map_var = Variable(
            type=VariableType(
                root_type=RootType.VECTOR, type_params=[instruction.item_type]
            ),
            value=[],
        )
        self.push_var(map_var)
        return self.get_instruction_pointer() + 1

    def instruction_vec_push(self) -> int:
        x = self.pop_var()
        vec: List[Variable] = self.top().value

        vec.append(x)
        return self.get_instruction_pointer() + 1

    def instruction_vec_pop(self) -> int:
        vec: List[Variable] = self.top().value

        x = vec.pop()
        self.push_var(x)

        return self.get_instruction_pointer() + 1

    def instruction_vec_get(self) -> int:
        x = self.pop_int()
        vec: List[Variable] = self.top().value

        self.push_var(vec[x])
        return self.get_instruction_pointer() + 1

    def instruction_vec_set(self) -> int:
        x: Any = self.pop_var()
        index = self.pop_int()
        vec: List[Variable] = self.top().value

        vec[index] = x
        return self.get_instruction_pointer() + 1

    def instruction_vec_size(self) -> int:
        vec: List[Variable] = self.top().value

        self.push_int(len(vec))
        return self.get_instruction_pointer() + 1

    def instruction_vec_empty(self) -> int:
        vec: List[Variable] = self.top().value

        self.push_bool(not bool(vec))
        return self.get_instruction_pointer() + 1

    def instruction_vec_clear(self) -> int:
        vec: List[Variable] = self.top().value

        vec.clear()
        return self.get_instruction_pointer() + 1

    def instruction_vec_copy(self) -> int:
        vec_var = self.top()
        copied = deepcopy(vec_var)
        self.push_var(copied)
        return self.get_instruction_pointer() + 1

    def instruction_map_get(self) -> int:
        key = self.pop_var()
        map: Dict[Variable, Variable] = self.top().value

        self.push_var(map[key])
        return self.get_instruction_pointer() + 1

    def instruction_map_set(self) -> int:
        value = self.pop_var()
        key = self.pop_var()
        map: Dict[Variable, Variable] = self.top().value

        map[key] = value
        return self.get_instruction_pointer() + 1

    def instruction_map_has_key(self) -> int:
        key = self.pop_var()
        map: Dict[Variable, Variable] = self.top().value

        self.push_bool(key in map)
        return self.get_instruction_pointer() + 1

    def instruction_map_size(self) -> int:
        map: Dict[Variable, Variable] = self.top().value

        self.push_int(len(map))
        return self.get_instruction_pointer() + 1

    def instruction_map_empty(self) -> int:
        map: Dict[Variable, Variable] = self.top().value

        self.push_bool(not bool(map))
        return self.get_instruction_pointer() + 1

    def instruction_map_pop(self) -> int:
        key = self.pop_var()
        map: Dict[Variable, Variable] = self.top().value

        self.push_var(map.pop(key))
        return self.get_instruction_pointer() + 1

    def instruction_map_drop(self) -> int:
        key = self.pop_var()
        map: Dict[Variable, Variable] = self.top().value

        del map[key]
        return self.get_instruction_pointer() + 1

    def instruction_map_clear(self) -> int:
        map: Dict[Variable, Variable] = self.top().value

        map.clear()
        return self.get_instruction_pointer() + 1

    def instruction_map_copy(self) -> int:
        map_var = self.top()
        copied = deepcopy(map_var)
        self.push_var(copied)
        return self.get_instruction_pointer() + 1

    def instruction_map_keys(self) -> int:  # pragma: nocover
        raise NotImplementedError

    def instruction_map_values(self) -> int:  # pragma: nocover
        raise NotImplementedError

    def instruction_push_struct(self, instruction: Instruction) -> int:
        assert isinstance(instruction, PushStruct)

        struct_fields: Dict[str, Variable] = {}

        # TODO move code to create zero value of struct out
        for field_name, var_type in instruction.type.fields.items():
            struct_fields[field_name] = Variable.zero_value(var_type)

        struct_var = Variable(
            type=VariableType(
                root_type=RootType.STRUCT,
                type_params=[],
                name=instruction.type.name,
            ),
            value=struct_fields,
        )
        self.push_var(struct_var)

        return self.get_instruction_pointer() + 1

    def instruction_get_struct_field(self, instruction: Instruction) -> int:
        field_name = self.pop_str()
        struct_fields: Dict[str, Variable] = self.top().value
        self.push_var(struct_fields[field_name])

        return self.get_instruction_pointer() + 1

    def instruction_set_struct_field(self, instruction: Instruction) -> int:
        assert isinstance(instruction, SetStructField)

        new_value: Variable = self.pop_var()
        field_name: str = self.pop_str()
        struct_fields: Dict[str, Variable] = self.top().value
        struct_fields[field_name] = new_value

        return self.get_instruction_pointer() + 1

    def instruction_stdandard_library_call(self, instruction: Instruction) -> int:
        assert isinstance(instruction, StandardLibraryCall)
        return self.stdlib_funcs[instruction.kind]()

    def instruction_syscall_exit(self) -> int:
        x = self.pop_int()
        exit(x)

    def instruction_syscall_getcwd(self) -> int:
        self.push_str(os.getcwd())

        return self.get_instruction_pointer() + 1

    def instruction_syscall_read(self) -> int:
        n = self.pop_int()
        fd = self.pop_int()

        try:
            read_data = os.read(fd, n).decode("utf-8")
        except OSError:
            self.push_str("")
            self.push_bool(False)
        else:
            self.push_str(read_data)
            self.push_bool(True)

        return self.get_instruction_pointer() + 1

    def instruction_syscall_time(self) -> int:
        unix_timestamp = int(time.time())
        self.push_int(unix_timestamp)

        return self.get_instruction_pointer() + 1

    def instruction_environ(self) -> int:
        value = {
            str_var(env_var_name): str_var(env_var_value)
            for env_var_name, env_var_value in os.environ.items()
        }

        env_vars_map = map_var(key_type=Str, value_type=Str, value=value)

        self.push_var(env_vars_map)
        return self.get_instruction_pointer() + 1

    def instruction_getenv(self) -> int:
        env_var_name: str = self.pop_var().value

        try:
            env_var_value = os.environ[env_var_name]
        except KeyError:
            self.push_str("")
            self.push_bool(False)
        else:
            self.push_str(env_var_value)
            self.push_bool(True)

        return self.get_instruction_pointer() + 1

    def instruction_setenv(self) -> int:
        env_var_value = self.pop_str()
        env_var_name = self.pop_str()

        os.environ[env_var_name] = env_var_value

        return self.get_instruction_pointer() + 1

    def instruction_unsetenv(self) -> int:
        env_var_name = self.pop_str()

        try:
            del os.environ[env_var_name]
        except KeyError:
            pass

        return self.get_instruction_pointer() + 1

    def instruction_syscall_chdir(self) -> int:
        dir_name = self.pop_str()

        try:
            os.chdir(dir_name)
        except OSError:
            self.push_var(bool_var(False))
        else:
            self.push_var(bool_var(True))

        return self.get_instruction_pointer() + 1

    def instruction_getpid(self) -> int:
        pid = os.getpid()
        self.push_int(pid)

        return self.get_instruction_pointer() + 1

    def instruction_getppid(self) -> int:
        ppid = os.getppid()
        self.push_int(ppid)

        return self.get_instruction_pointer() + 1

    def instruction_open(self) -> int:
        mode = self.pop_int()
        flags = self.pop_int()
        path = self.pop_str()

        try:
            fd = os.open(path=path, flags=flags, mode=mode)
        except Exception:
            self.push_int(0)
            self.push_bool(False)
        else:
            self.push_int(fd)
            self.push_bool(True)

        return self.get_instruction_pointer() + 1

    def instruction_syscall_close(self) -> int:
        fd = self.pop_int()

        try:
            os.close(fd)
        except Exception:
            self.push_bool(False)
        else:
            self.push_bool(True)

        return self.get_instruction_pointer() + 1

    def instruction_write(self) -> int:
        data = self.pop_str()
        fd = self.pop_int()

        try:
            written = os.write(fd, bytes(data, encoding="utf-8"))
        except Exception:
            self.push_int(0)
            self.push_bool(False)
        else:
            self.push_int(written)
            self.push_bool(True)

        return self.get_instruction_pointer() + 1

    def instruction_syscall_execve(self) -> int:
        stack_env: Dict[Variable, Variable] = self.pop_var().value
        stack_argv: List[Variable] = self.pop_var().value
        path: str = self.pop_var().value

        env: Dict[str, str] = {
            key.value: value.value for (key, value) in stack_env.items()
        }
        argv: List[str] = [item.value for item in stack_argv]

        os.execve(path, argv, env)
        return self.get_instruction_pointer() + 1

    def instruction_syscall_fork(self) -> int:
        pid = os.fork()
        self.push_int(pid)

        return self.get_instruction_pointer() + 1

    def instruction_waitpid(self) -> int:
        options = self.pop_int()
        pid = self.pop_int()

        try:
            _, wait_status = os.waitpid(pid, options)
            exit_code = os.waitstatus_to_exitcode(wait_status)
        except OSError:
            self.push_int(0)
            self.push_bool(False)
        else:
            self.push_int(exit_code)
            self.push_bool(True)

        return self.get_instruction_pointer() + 1

    def instruction_str_strip(self) -> int:
        string = self.pop_str()
        self.push_str(string.strip())

        return self.get_instruction_pointer() + 1

    def instruction_str_split(self) -> int:
        separator = self.pop_str()
        string: str = self.top().value

        split = string.split(separator)

        split_var = vec_var(
            item_type=Str, value=[str_var(split_item) for split_item in split]
        )

        self.push_var(split_var)

        return self.get_instruction_pointer() + 1

    def instruction_syscall_fsync(self) -> int:
        fd = self.pop_int()

        try:
            os.fsync(fd)
        except OSError:
            self.push_bool(False)
        else:
            self.push_bool(True)

        return self.get_instruction_pointer() + 1

    def instruction_str_substr(self) -> int:
        end = self.pop_int()
        start = self.pop_int()
        string: str = self.top().value

        if (
            start < 0
            or end < 0
            or start > len(string)
            or end > len(string)
            or end < start
        ):
            self.push_str("")
            self.push_bool(False)
        else:
            self.push_str(string[start:end])
            self.push_bool(True)

        return self.get_instruction_pointer() + 1

    def instruction_str_len(self) -> int:
        string: str = self.top().value
        self.push_int(len(string))
        return self.get_instruction_pointer() + 1

    def instruction_str_upper(self) -> int:
        string: str = self.top().value
        self.push_str(string.upper())
        return self.get_instruction_pointer() + 1

    def instruction_str_lower(self) -> int:
        string: str = self.top().value
        self.push_str(string.lower())
        return self.get_instruction_pointer() + 1

    def instruction_str_find(self) -> int:
        search = self.pop_str()
        string: str = self.top().value

        index = string.find(search)

        if index == -1:
            self.push_int(0)
            self.push_bool(False)
        else:
            self.push_int(index)
            self.push_bool(True)

        return self.get_instruction_pointer() + 1

    def instruction_str_find_after(self) -> int:
        offset = self.pop_int()
        search = self.pop_str()
        string: str = self.top().value

        index = string.find(search, offset)

        if index == -1:
            self.push_int(0)
            self.push_bool(False)
        else:
            self.push_int(index)
            self.push_bool(True)

        return self.get_instruction_pointer() + 1

    def instruction_str_to_int(self) -> int:
        string: str = self.top().value

        try:
            integer = int(string)
        except ValueError:
            self.push_int(0)
            self.push_bool(False)
        else:
            self.push_int(integer)
            self.push_bool(True)

        return self.get_instruction_pointer() + 1

    def instruction_str_join(self) -> int:
        parts: List[Variable] = self.pop_var().value
        string: str = self.top().value

        joined = string.join(part.value for part in parts)

        self.push_str(joined)

        return self.get_instruction_pointer() + 1

    def instruction_str_equals(self) -> int:
        other = self.pop_str()
        string: str = self.top().value

        self.push_bool(string == other)

        return self.get_instruction_pointer() + 1

    def instruction_str_contains(self) -> int:
        other = self.pop_str()
        string: str = self.top().value

        self.push_bool(other in string)

        return self.get_instruction_pointer() + 1

    def instruction_str_to_bool(self) -> int:
        string: str = self.top().value

        if string in ["true", "false"]:
            self.push_bool(string == "true")
            self.push_bool(True)
        else:
            self.push_bool(False)
            self.push_bool(False)

        return self.get_instruction_pointer() + 1

    def instruction_str_replace(self) -> int:
        replacement = self.pop_str()
        search = self.pop_str()
        string: str = self.top().value

        replaced = string.replace(search, replacement)
        self.push_str(replaced)

        return self.get_instruction_pointer() + 1

    def instruction_str_append(self) -> int:
        suffix = self.pop_str()
        string: str = self.top().value

        appeneded = string + suffix
        self.push_str(appeneded)

        return self.get_instruction_pointer() + 1

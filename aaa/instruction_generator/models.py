from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple

from aaa import AaaModel
from aaa.cross_referencer.models import Function, Type, VariableType


class StandardLibraryCallKind(Enum):
    ENVIRON = "ENVIRON"
    GETENV = "GETENV"
    GETTIMEOFDAY = "GETTIMEOFDAY"
    MAP_CLEAR = "MAP_CLEAR"
    MAP_COPY = "MAP_COPY"
    MAP_DROP = "MAP_DROP"
    MAP_EMPTY = "MAP_EMPTY"
    MAP_GET = "MAP_GET"
    MAP_HAS_KEY = "MAP_HAS_KEY"
    MAP_KEYS = "MAP_KEYS"
    MAP_POP = "MAP_POP"
    MAP_SET = "MAP_SET"
    MAP_SIZE = "MAP_SIZE"
    MAP_VALUES = "MAP_VALUES"
    SETENV = "SETENV"
    STR_APPEND = "STR_APPEND"
    STR_CONTAINS = "STR_CONTAINS"
    STR_EQUALS = "STR_EQUALS"
    STR_FIND = "STR_FIND"
    STR_FIND_AFTER = "STR_FIND_AFTER"
    STR_JOIN = "STR_JOIN"
    STR_LEN = "STR_LEN"
    STR_LOWER = "STR_LOWER"
    STR_REPLACE = "STR_REPLACE"
    STR_SPLIT = "STR_SPLIT"
    STR_STRIP = "STR_STRIP"
    STR_SUBSTR = "STR_SUBSTR"
    STR_TO_BOOL = "STR_TO_BOOL"
    STR_TO_INT = "STR_TO_INT"
    STR_UPPER = "STR_UPPER"
    SYSCALL_ACCEPT = "SYSCALL_ACCEPT"
    SYSCALL_BIND = "SYSCALL_BIND"
    SYSCALL_CHDIR = "SYSCALL_CHDIR"
    SYSCALL_CLOSE = "SYSCALL_CLOSE"
    SYSCALL_CONNECT = "SYSCALL_CONNECT"
    SYSCALL_EXECVE = "SYSCALL_EXECVE"
    SYSCALL_EXIT = "SYSCALL_EXIT"
    SYSCALL_FORK = "SYSCALL_FORK"
    SYSCALL_FSYNC = "SYSCALL_FSYNC"
    SYSCALL_GETCWD = "SYSCALL_GETCWD"
    SYSCALL_GETPID = "SYSCALL_GETPID"
    SYSCALL_GETPPID = "SYSCALL_GETPPID"
    SYSCALL_LISTEN = "SYSCALL_LISTEN"
    SYSCALL_OPEN = "SYSCALL_OPEN"
    SYSCALL_READ = "SYSCALL_READ"
    SYSCALL_SOCKET = "SYSCALL_SOCKET"
    SYSCALL_TIME = "SYSCALL_TIME"
    SYSCALL_UNLINK = "SYSCALL_UNLINK"
    SYSCALL_WAITPID = "SYSCALL_WAITPID"
    SYSCALL_WRITE = "SYSCALL_WRITE"
    UNSETENV = "UNSETENV"
    VEC_CLEAR = "VEC_CLEAR"
    VEC_COPY = "VEC_COPY"
    VEC_EMPTY = "VEC_EMPTY"
    VEC_GET = "VEC_GET"
    VEC_POP = "VEC_POP"
    VEC_PUSH = "VEC_PUSH"
    VEC_SET = "VEC_SET"
    VEC_SIZE = "VEC_SIZE"


class Instruction(AaaModel):
    ...


class PushInt(Instruction):
    def __init__(self, value: int) -> None:
        self.value = value

    def __repr__(self) -> str:  # pragma: nocover
        return f"{type(self).__name__}({self.value})"


class Plus(Instruction):
    ...


class Minus(Instruction):
    ...


class Multiply(Instruction):
    ...


class Divide(Instruction):
    ...


class PushBool(Instruction):
    def __init__(self, value: bool) -> None:
        self.value = value

    def __repr__(self) -> str:  # pragma: nocover
        value = "true" if self.value else "false"
        return f"{type(self).__name__}({value})"


class And(Instruction):
    ...


class Or(Instruction):
    ...


class Not(Instruction):
    ...


class Equals(Instruction):
    ...


class IntGreaterThan(Instruction):
    ...


class IntGreaterEquals(Instruction):
    ...


class IntLessThan(Instruction):
    ...


class IntLessEquals(Instruction):
    ...


class IntNotEqual(Instruction):
    ...


class Drop(Instruction):
    ...


class Dup(Instruction):
    ...


class Swap(Instruction):
    ...


class Over(Instruction):
    ...


class Rot(Instruction):
    ...


class Print(Instruction):
    ...


class PushString(Instruction):
    def __init__(self, value: str) -> None:
        self.value = value

    def __repr__(self) -> str:  # pragma: nocover
        return f'{type(self).__name__}("{self.value}")'


class Modulo(Instruction):
    ...


class CallFunction(Instruction):
    def __init__(self, func_name: str, file: Path) -> None:
        self.func_name = func_name
        self.file = file

    def __repr__(self) -> str:  # pragma: nocover
        return f"{type(self).__name__}('{self.func_name}')"


class PushFunctionArgument(Instruction):
    def __init__(self, arg_name: str) -> None:
        self.arg_name = arg_name


class Jump(Instruction):
    def __init__(self, instruction_offset: int) -> None:
        self.instruction_offset = instruction_offset

    def __repr__(self) -> str:  # pragma: nocover
        return f"{type(self).__name__}({self.instruction_offset})"


class JumpIfNot(Instruction):
    def __init__(self, instruction_offset: int) -> None:
        self.instruction_offset = instruction_offset

    def __repr__(self) -> str:  # pragma: nocover
        return f"{type(self).__name__}({self.instruction_offset})"


class Nop(Instruction):
    ...


class Assert(Instruction):
    ...


class PushVec(Instruction):
    def __init__(self, item_type: VariableType) -> None:
        self.item_type = item_type


class PushMap(Instruction):
    def __init__(self, key_type: VariableType, value_type: VariableType) -> None:
        self.key_type = key_type
        self.value_type = value_type


class StandardLibraryCall(Instruction):
    def __init__(self, kind: StandardLibraryCallKind) -> None:
        self.kind = kind


class PushStruct(Instruction):
    def __init__(self, var_type: VariableType) -> None:
        self.var_type = var_type


class GetStructField(Instruction):
    ...


class SetStructField(Instruction):
    ...


class InstructionGeneratorOutput:
    def __init__(
        self,
        instructions: Dict[Tuple[Path, str], List[Instruction]],
        types: Dict[Tuple[Path, str], Type],
        functions: Dict[Tuple[Path, str], Function],
        entrypoint: Path,
        builtins_path: Path,
    ) -> None:
        self.instructions = instructions
        self.types = types
        self.functions = functions
        self.entrypoint = entrypoint
        self.builtins_path = builtins_path

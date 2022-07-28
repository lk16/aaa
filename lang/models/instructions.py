from enum import Enum
from pathlib import Path

from lang.models import AaaModel
from lang.models.parse import Struct
from lang.typing.types import VariableType


class StandardLibraryCallKind(Enum):
    ENVIRON = "ENVIRON"
    GETENV = "GETENV"
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
    SYSCALL_CHDIR = "SYSCALL_CHDIR"
    SYSCALL_CLOSE = "SYSCALL_CLOSE"
    SYSCALL_EXIT = "SYSCALL_EXIT"
    SYSCALL_EXECVE = "SYSCALL_EXECVE"
    SYSCALL_FORK = "SYSCALL_FORK"
    SYSCALL_GETCWD = "SYSCALL_GETCWD"
    SYSCALL_GETPID = "SYSCALL_GETPID"
    SYSCALL_GETPPID = "SYSCALL_GETPPID"
    SYSCALL_OPEN = "SYSCALL_OPEN"
    SYSCALL_READ = "SYSCALL_READ"
    SYSCALL_TIME = "SYSCALL_TIME"
    SYSCALL_WRITE = "SYSCALL_WRITE"
    SYSCALL_WAITPID = "SYSCALL_WAITPID"
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
    class Config:
        arbitrary_types_allowed = True  # TODO fix


class PushInt(Instruction):
    value: int

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
    value: bool

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
    value: str

    def __repr__(self) -> str:  # pragma: nocover
        return f'{type(self).__name__}("{self.value}")'


class Modulo(Instruction):
    ...


class CallFunction(Instruction):
    func_name: str
    file: Path

    def __repr__(self) -> str:  # pragma: nocover
        return f"{type(self).__name__}('{self.func_name}')"


class PushFunctionArgument(Instruction):
    arg_name: str


class Jump(Instruction):
    instruction_offset: int

    def __repr__(self) -> str:  # pragma: nocover
        return f"{type(self).__name__}({self.instruction_offset})"


class JumpIfNot(Instruction):
    instruction_offset: int

    def __repr__(self) -> str:  # pragma: nocover
        return f"{type(self).__name__}({self.instruction_offset})"


class Nop(Instruction):
    ...


class Assert(Instruction):
    ...


class PushVec(Instruction):
    item_type: VariableType


class PushMap(Instruction):
    key_type: VariableType
    value_type: VariableType


class StandardLibraryCall(Instruction):
    kind: StandardLibraryCallKind


class PushStruct(Instruction):
    type: Struct


class GetStructField(Instruction):
    ...


class SetStructField(Instruction):
    ...

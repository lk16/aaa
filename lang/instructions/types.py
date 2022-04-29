from dataclasses import dataclass
from pathlib import Path

from lang.typing.types import VariableType


@dataclass
class Instruction:
    ...


@dataclass
class PushInt(Instruction):
    value: int

    def __repr__(self) -> str:  # pragma: nocover
        return f"{type(self).__name__}({self.value})"


@dataclass
class Plus(Instruction):
    ...


@dataclass
class Minus(Instruction):
    ...


@dataclass
class Multiply(Instruction):
    ...


@dataclass
class Divide(Instruction):
    ...


@dataclass
class PushBool(Instruction):
    value: bool

    def __repr__(self) -> str:  # pragma: nocover
        value = "true" if self.value else "false"
        return f"{type(self).__name__}({value})"


@dataclass
class And(Instruction):
    ...


@dataclass
class Or(Instruction):
    ...


@dataclass
class Not(Instruction):
    ...


@dataclass
class Equals(Instruction):
    ...


@dataclass
class IntGreaterThan(Instruction):
    ...


@dataclass
class IntGreaterEquals(Instruction):
    ...


@dataclass
class IntLessThan(Instruction):
    ...


@dataclass
class IntLessEquals(Instruction):
    ...


@dataclass
class IntNotEqual(Instruction):
    ...


@dataclass
class Drop(Instruction):
    ...


@dataclass
class Dup(Instruction):
    ...


@dataclass
class Swap(Instruction):
    ...


@dataclass
class Over(Instruction):
    ...


@dataclass
class Rot(Instruction):
    ...


@dataclass
class Print(Instruction):
    ...


@dataclass
class PushString(Instruction):
    value: str

    def __repr__(self) -> str:  # pragma: nocover
        return f'{type(self).__name__}("{self.value}")'


@dataclass
class SubString(Instruction):
    ...


@dataclass
class Modulo(Instruction):
    ...


@dataclass
class StringLength(Instruction):
    ...


@dataclass
class CallFunction(Instruction):
    func_name: str
    file: Path

    def __repr__(self) -> str:  # pragma: nocover
        return f"{type(self).__name__}('{self.func_name}')"


@dataclass
class PushFunctionArgument(Instruction):
    arg_name: str


@dataclass
class Jump(Instruction):
    instruction_offset: int

    def __repr__(self) -> str:  # pragma: nocover
        return f"{type(self).__name__}({self.instruction_offset})"


@dataclass
class JumpIfNot(Instruction):
    instruction_offset: int

    def __repr__(self) -> str:  # pragma: nocover
        return f"{type(self).__name__}({self.instruction_offset})"


@dataclass
class Nop(Instruction):
    ...


@dataclass
class Assert(Instruction):
    ...


@dataclass
class PushVec(Instruction):
    item_type: VariableType


@dataclass
class PushMap(Instruction):
    key_type: VariableType
    value_type: VariableType


@dataclass
class VecPush(Instruction):
    ...


@dataclass
class VecPop(Instruction):
    ...


@dataclass
class VecGet(Instruction):
    ...


@dataclass
class VecSet(Instruction):
    ...

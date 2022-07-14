from pathlib import Path

from lang.parse.models import AaaModel, Struct
from lang.typing.types import VariableType


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


class VecPush(Instruction):
    ...


class VecPop(Instruction):
    ...


class VecGet(Instruction):
    ...


class VecSet(Instruction):
    ...


class VecSize(Instruction):
    ...


class VecEmpty(Instruction):
    ...


class VecClear(Instruction):
    ...


class VecCopy(Instruction):
    ...


class MapGet(Instruction):
    ...


class MapSet(Instruction):
    ...


class MapHasKey(Instruction):
    ...


class MapSize(Instruction):
    ...


class MapEmpty(Instruction):
    ...


class MapPop(Instruction):
    ...


class MapDrop(Instruction):
    ...


class MapClear(Instruction):
    ...


class MapCopy(Instruction):
    ...


class MapKeys(Instruction):
    ...


class MapValues(Instruction):
    ...


class PushStruct(Instruction):
    type: Struct


class GetStructField(Instruction):
    ...


class SetStructField(Instruction):
    ...

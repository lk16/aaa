from dataclasses import dataclass
from typing import Optional


@dataclass
class Instruction:
    ...


@dataclass
class IntPush(Instruction):
    value: int


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
class BoolPush(Instruction):
    value: bool


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
class If(Instruction):
    # Instruction to jump to if the condition is false.
    # Initialization is done when we find a corresponding operation ("else" or "end") while parsing.
    jump_if_false: Optional[int]


@dataclass
class Else(Instruction):
    # Instruction to jump to if the condition is false.
    # Initialization is done when we find corresponding "end" while parsing.
    jump_end: Optional[int]


@dataclass
class End(Instruction):
    ...


@dataclass
class CharNewLinePrint(Instruction):
    ...


@dataclass
class Print(Instruction):
    ...


@dataclass
class While(Instruction):
    # Instruction to jump to if the condition is false.
    # Initialization is done when we find corresponding "end" while parsing.
    jump_end: Optional[int]


@dataclass
class WhileEnd(Instruction):
    jump_start: int


@dataclass
class StringPush(Instruction):
    value: str


@dataclass
class SubString(Instruction):
    ...


@dataclass
class Modulo(Instruction):
    ...


@dataclass
class StringLength(Instruction):
    ...

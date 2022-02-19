from dataclasses import dataclass
from typing import Optional


@dataclass
class Operation:
    ...


@dataclass
class UnhandledOperation(Operation):
    # TODO: move to tests folder
    # This exists for testing purposes
    ...


@dataclass
class IntPush(Operation):
    value: int


@dataclass
class IntPrint(Operation):
    ...


@dataclass
class Plus(Operation):
    ...


@dataclass
class Minus(Operation):
    ...


@dataclass
class Multiply(Operation):
    ...


@dataclass
class Divide(Operation):
    ...


@dataclass
class BoolPush(Operation):
    value: bool


@dataclass
class And(Operation):
    ...


@dataclass
class Or(Operation):
    ...


@dataclass
class Not(Operation):
    ...


@dataclass
class BoolPrint(Operation):
    ...


@dataclass
class IntEquals(Operation):
    ...


@dataclass
class IntGreaterThan(Operation):
    ...


@dataclass
class IntGreaterEquals(Operation):
    ...


@dataclass
class IntLessThan(Operation):
    ...


@dataclass
class IntLessEquals(Operation):
    ...


@dataclass
class IntNotEqual(Operation):
    ...


@dataclass
class Drop(Operation):
    ...


@dataclass
class Dup(Operation):
    ...


@dataclass
class Swap(Operation):
    ...


@dataclass
class Over(Operation):
    ...


@dataclass
class Rot(Operation):
    ...


@dataclass
class If(Operation):
    # Instruction to jump to if the condition is false.
    # Initialization is done when we find corresponding operations (else/end) while parsing.
    jump_if_false: Optional[int]


@dataclass
class End(Operation):
    ...


@dataclass
class CharNewLinePrint(Operation):
    ...

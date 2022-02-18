from dataclasses import dataclass


@dataclass
class Operation:
    ...


@dataclass
class UnhandledOperation(Operation):
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

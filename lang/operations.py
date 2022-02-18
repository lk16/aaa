from dataclasses import dataclass


@dataclass
class Operation:
    ...


@dataclass
class UnhandledOperation(Operation):
    # This exists for testing purposes
    ...


@dataclass
class PushInt(Operation):
    value: int


@dataclass
class PrintInt(Operation):
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

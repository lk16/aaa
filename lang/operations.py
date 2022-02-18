from dataclasses import dataclass


@dataclass
class Operation:
    ...


@dataclass
class PushInt(Operation):
    value: int


class PrintInt(Operation):
    ...

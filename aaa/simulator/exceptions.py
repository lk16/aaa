from typing import List

from aaa import AaaException
from aaa.simulator.models import CallStackItem


class AaaRuntimeException(AaaException):
    ...


class AaaAssertionFailure(AaaRuntimeException):
    def __init__(self, call_stack: List[CallStackItem]) -> None:
        self.call_stack = call_stack

    def __str__(self) -> str:
        # TODO put better message
        return "Assertion failure\n"

from typing import List

from aaa import AaaException, Position
from aaa.simulator.models import CallStackItem


class AaaRuntimeException(AaaException):
    ...


class AaaAssertionFailure(AaaRuntimeException):
    def __init__(self, position: Position, call_stack: List[CallStackItem]) -> None:
        self.position = position
        self.call_stack = call_stack

    def __str__(self) -> str:
        msg = f"{self.position}: Assertion failure, stacktrace:\n"

        for call_stack_item in reversed(self.call_stack):
            # TODO add location of calls
            msg += f"- {call_stack_item.function.name}\n"

        return msg

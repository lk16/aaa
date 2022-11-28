from pathlib import Path
from typing import List

from aaa import AaaException
from aaa.simulator.models import CallStackItem


class AaaRuntimeException(AaaException):
    ...


class AaaAssertionFailure(AaaRuntimeException):
    def __init__(
        self, file: Path, line: int, column: int, call_stack: List[CallStackItem]
    ) -> None:
        self.file = file
        self.line = line
        self.column = column
        self.call_stack = call_stack

    def __str__(self) -> str:
        msg = f"{self.file}:{self.line}:{self.column}: Assertion failure, stacktrace:\n"

        for call_stack_item in reversed(self.call_stack):
            # TODO add location of calls
            msg += f"- {call_stack_item.function.name}\n"

        return msg

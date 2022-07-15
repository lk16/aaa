from typing import List

from lang.exceptions import AaaRuntimeException
from lang.models.runtime import CallStackItem


class AaaAssertionFailure(AaaRuntimeException):
    def __init__(self, call_stack: List[CallStackItem]) -> None:
        self.call_stack = call_stack

    def __str__(self) -> str:
        msg = "Assertion failure, stacktrace:\n"

        for call_stack_item in self.call_stack:
            name = call_stack_item.func_name

            args = ""
            if call_stack_item.argument_values:  # pragma: nocover
                args = ", arguments: " + ", ".join(
                    f"{name}={value.__repr__()}"
                    for name, value in call_stack_item.argument_values.items()
                )

            msg += f"- {name}{args}"

        return msg

from typing import Optional

from aaa.simulator.variable import Variable


def format_stack_item(var: Variable) -> str:  # pragma: nocover
    # TODO consider using __repr__() methods
    raise NotImplementedError


def format_str(string: str, max_length: Optional[int] = None) -> str:  # pragma: nocover
    string = string.replace("\n", "\\n")

    if max_length is not None and len(string) > max_length:
        string = string[: max_length - 1] + "…"

    return string

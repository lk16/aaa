from typing import Optional

from lang.typing.types import StackItem


def format_stack_item(item: StackItem) -> str:  # pragma: nocover
    # TODO consider using __repr__() methods

    if isinstance(item, bool):
        if item:
            return "true"
        return "false"

    if isinstance(item, int):
        return str(item)

    if isinstance(item, str):
        item = item.replace("\n", "\\n").replace('"', '\\"')
        return f'"{item}"'

    raise NotADirectoryError


def format_str(string: str, max_length: Optional[int] = None) -> str:  # pragma: nocover
    string = string.replace("\n", "\\n")

    if max_length is not None and len(string) > max_length:
        string = string[: max_length - 1] + "…"

    return string

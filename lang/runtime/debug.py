from typing import Optional

from lang.typing.types import RootType, Variable


def format_stack_item(var: Variable) -> str:  # pragma: nocover
    # TODO consider using __repr__() methods

    if var.has_root_type(RootType.BOOL):
        if var.value:
            return "true"
        return "false"

    elif var.has_root_type(RootType.INTEGER):
        return str(var.value)

    elif var.has_root_type(RootType.STRING):
        formatted = var.value.replace("\n", "\\n").replace('"', '\\"')
        return f'"{formatted}"'

    else:  # pragma: nocover
        assert False


def format_str(string: str, max_length: Optional[int] = None) -> str:  # pragma: nocover
    string = string.replace("\n", "\\n")

    if max_length is not None and len(string) > max_length:
        string = string[: max_length - 1] + "…"

    return string

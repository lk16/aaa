from typing import Sequence

from lang.typing.types import TypePlaceholder, VariableType


class AaaException(Exception):
    def __str__(self) -> str:  # pragma: nocover
        raise NotImplementedError


class AaaLoadException(AaaException):
    ...


class AaaRuntimeException(AaaException):
    ...


def format_typestack(
    type_stack: Sequence[VariableType | TypePlaceholder],
) -> str:  # pragma: nocover
    return " ".join(repr(type_stack_item) for type_stack_item in type_stack)

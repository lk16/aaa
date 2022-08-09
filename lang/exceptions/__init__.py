from pathlib import Path
from typing import Sequence

from lark.lexer import Token

from lang.models.typing.var_type import VariableType


class AaaException(Exception):
    ...


class AaaLoadException(AaaException):
    ...


class AaaRuntimeException(AaaException):
    ...


class NamingException(AaaLoadException):
    ...


def format_typestack(
    type_stack: Sequence[VariableType],
) -> str:
    return " ".join(repr(type_stack_item) for type_stack_item in type_stack)


def error_location(file: Path, token: Token) -> str:
    return f"{file}:{token.line}:{token.column}"

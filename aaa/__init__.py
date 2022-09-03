from pathlib import Path

from lark.lexer import Token


class AaaModel:
    ...


class AaaException(Exception):
    ...


def error_location(file: Path, token: Token) -> str:
    return f"{file}:{token.line}:{token.column}"

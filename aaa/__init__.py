from pathlib import Path

from lark.lexer import Token


class AaaModel:
    ...


class AaaException(Exception):
    ...


def error_location(file: Path, token: Token) -> str:
    cwd = Path.cwd()

    if cwd in file.parents:
        nicer_file = file.relative_to(cwd)
    else:
        nicer_file = file

    return f"{nicer_file}:{token.line}:{token.column}"

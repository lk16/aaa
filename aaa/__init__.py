from pathlib import Path
from typing import Sequence

from lark.lexer import Token


class AaaModel:
    def __repr__(self) -> str:
        return (
            f"{type(self).__qualname__}("
            + ", ".join(
                f"{field_name}: {repr(field)}"
                for field_name, field in vars(self).items()
            )
            + ")"
        )


class AaaException(Exception):
    ...


class AaaRunnerException(AaaException):
    def __init__(self, exceptions: Sequence[AaaException]) -> None:
        self.exceptions = exceptions


def error_location(file: Path, token: Token) -> str:
    cwd = Path.cwd()

    if cwd in file.parents:
        nicer_file = file.relative_to(cwd)
    else:
        nicer_file = file

    return f"{nicer_file}:{token.line}:{token.column}"

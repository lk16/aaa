from pathlib import Path
from typing import Sequence


class AaaModel:
    def __repr__(self) -> str:  # pragma: nocover
        return (
            f"{type(self).__qualname__}("
            + ", ".join(
                f"{field_name}: {repr(field)}"
                for field_name, field in vars(self).items()
            )
            + ")"
        )


class Position:
    def __init__(self, file: Path, line: int, column: int) -> None:
        self.file = file
        self.line = line
        self.column = column

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"

    def __hash__(self) -> int:
        return hash((self.file, self.line, self.column))


class AaaException(Exception):
    ...


class AaaRunnerException(AaaException):
    def __init__(self, exceptions: Sequence[AaaException]) -> None:
        self.exceptions = exceptions


class AaaRuntimeException(AaaException):
    ...

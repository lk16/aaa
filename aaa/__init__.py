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


class AaaException(Exception):
    ...


class AaaRunnerException(AaaException):
    def __init__(self, exceptions: Sequence[AaaException]) -> None:
        self.exceptions = exceptions


def error_location(file: Path, line: int, column: int) -> str:
    return f"{file}:{line}:{column}"

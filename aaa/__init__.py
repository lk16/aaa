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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Position):
            return False

        return str(self) == str(other)

    def context(self) -> str:  # pragma: nocover
        code = self.file.read_text()
        line = code.split("\n")[self.line - 1]
        return line + "\n" + ((self.column - 1) * " ") + "^\n"

    def short_filename(self) -> str:  # pragma: nocover
        try:
            short = self.file.relative_to(Path.cwd())
        except ValueError:
            # It is possible the file is not in the subpath of cwd
            # We just print the absolute path then
            short = self.file

        return str(short)

    def __lt__(self, other: "Position") -> bool:
        return (self.file, self.line, self.column) < (
            other.file,
            other.line,
            other.column,
        )


class AaaException(Exception):
    ...


class AaaRunnerException(AaaException):
    def __init__(self, exceptions: Sequence[AaaException]) -> None:
        self.exceptions = exceptions


class AaaRuntimeException(AaaException):
    ...

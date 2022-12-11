from pathlib import Path

from aaa import AaaException, error_location


class BaseTokenizerException(AaaException):
    ...


class TokenizerException(BaseTokenizerException):
    def __init__(self, file: Path, line: int, column: int) -> None:
        self.file = file
        self.line = line
        self.column = column

    def where(self) -> str:  # pragma: nocover
        return error_location(self.file, self.line, self.column)

    def context(self) -> str:  # pragma: nocover
        line = self.file.read_text().split("\n")[self.line - 1]
        return line + "\n" + ((self.column - 1) * " ") + "^\n"

    def __str__(self) -> str:  # pragma: nocover
        # TODO confirm this looks correct
        return f"{self.where()} Tokenizing failed\n{self.context()}\n"


class FileReadError(BaseTokenizerException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f"{self.file}: Failed to open or read\n"

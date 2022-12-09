from pathlib import Path

from aaa import AaaException, error_location


class TokenizerException(AaaException):
    def __init__(self, file: Path, line: int, column: int) -> None:
        self.file = file
        self.line = line
        self.column = column

    def where(self) -> str:
        return error_location(self.file, self.line, self.column)

    def context(self) -> str:
        line = self.file.read_text().split("\n")[self.line - 1]
        return line + "\n" + ((self.column - 1) * " ") + "^\n"

    def __str__(self) -> str:
        return f"{self.where()} Tokenizing failed\n{self.context()}\n"

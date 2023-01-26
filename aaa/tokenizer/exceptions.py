from pathlib import Path

from aaa import AaaException, Position


class BaseTokenizerException(AaaException):
    ...


class TokenizerException(BaseTokenizerException):
    def __init__(self, position: Position) -> None:
        self.position = position

    def context(self) -> str:  # pragma: nocover
        # TODO move context into Position
        code = self.position.file.read_text()
        line = code.split("\n")[self.position.line - 1]
        return line + "\n" + ((self.position.column - 1) * " ") + "^\n"

    def __str__(self) -> str:  # pragma: nocover
        return f"{self.position}: Tokenizing failed\n{self.context()}\n"


class FileReadError(BaseTokenizerException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f"{self.file}: Failed to open or read\n"

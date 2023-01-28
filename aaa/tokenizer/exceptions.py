from pathlib import Path

from aaa import AaaException, Position


class TokenizerBaseException(AaaException):
    ...


class TokenizerException(TokenizerBaseException):
    def __init__(self, position: Position) -> None:
        self.position = position

    def __str__(self) -> str:  # pragma: nocover
        return f"{self.position}: Tokenizing failed\n{self.position.context()}\n"


class FileReadError(TokenizerBaseException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f"{self.file}: Failed to open or read\n"

from pathlib import Path

from aaa import AaaException
from aaa.parser.lib.exceptions import ParseError, TokenizerException


class AaaParserBaseException(AaaException):
    def __init__(self, child: ParseError | TokenizerException):
        self.child = child

    def __str__(self) -> str:
        return str(self.child)


class FileReadError(AaaParserBaseException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f"{self.file}: Could not read file. It may not exist.\n"

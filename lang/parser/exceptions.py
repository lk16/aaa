from pathlib import Path

from lark.exceptions import UnexpectedInput
from lark.lexer import Token

from lang import AaaException


class ParserBaseException(AaaException):
    ...


class ParseException(ParserBaseException):
    def __init__(self, *, file: Path, parse_error: UnexpectedInput) -> None:
        self.parse_error = parse_error
        self.file = file

    def where(self) -> str:
        return f"{self.file}:{self.parse_error.line}:{self.parse_error.column}"

    def __str__(self) -> str:
        context = self.parse_error.get_context(self.file.read_text())

        return f"{self.where()}: Could not parse file\n" + context


class KeywordUsedAsIdentifier(ParserBaseException):
    def __init__(self, *, token: Token, file: Path) -> None:
        self.token = token
        self.file = file

    def where(self) -> str:
        return f"{self.file}:{self.token.line}:{self.token.column}"

    def __str__(self) -> str:
        return f'{self.where()}: Can\'t use keyword "{self.token.value}" as identifier.'


class FileReadError(ParserBaseException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f"{self.file}: Failed to open or read\n"

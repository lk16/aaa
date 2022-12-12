from pathlib import Path
from typing import List

from aaa import AaaException, Position
from aaa.tokenizer.models import TokenType


class ParserBaseException(AaaException):
    ...


class ParserException(ParserBaseException):
    def __init__(
        self,
        position: Position,
        expected_token_types: List[TokenType],
        found_token_type: TokenType,
    ) -> None:
        self.position = position
        self.expected_token_types = expected_token_types
        self.found_token_types = found_token_type

    def context(self) -> str:  # pragma: nocover
        code = self.position.file.read_text()
        line = code.split("\n")[self.position.line - 1]
        return line + "\n" + ((self.position.column - 1) * " ") + "^\n"

    def __str__(self) -> str:  # pragma: nocover
        expected = ", ".join(
            token_type.name for token_type in self.expected_token_types
        )
        found = self.found_token_types.name

        message = f"{self.position}: Parsing failed, expected "

        if len(self.expected_token_types) > 1:
            message += "one of "

        message += f"{expected}, but found {found}\n" + self.context() + "\n"
        return message


class EndOfFileException(ParserBaseException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        # TODO add context
        return f"{self.file} Parsing failed, unexpected end of file."


class NewParserUnhandledTopLevelToken(ParserBaseException):
    def __init__(self, position: Position, token_type: TokenType) -> None:
        self.position = position
        self.token_type = token_type

    def context(self) -> str:  # pragma: nocover
        code = self.position.file.read_text()
        line = code.split("\n")[self.position.line - 1]
        return line + "\n" + ((self.position.column - 1) * " ") + "^\n"

    def __str__(self) -> str:  # pragma: nocover
        return (
            f"{self.position}: Parsing failed, unexpected top-level token {self.token_type.name}\n"
            + self.context()
            + "\n"
        )

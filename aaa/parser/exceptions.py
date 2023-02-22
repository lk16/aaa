from pathlib import Path
from typing import List

from aaa import AaaException, Position
from aaa.tokenizer.models import Token, TokenType


class ParserBaseException(AaaException):
    ...


class ParserException(ParserBaseException):
    def __init__(self, token: Token, expected_token_types: List[TokenType]) -> None:
        self.token = token
        self.expected_token_types = expected_token_types

    def __str__(self) -> str:  # pragma: nocover
        expected = ", ".join(
            token_type.name for token_type in self.expected_token_types
        )
        found = self.token.type.name

        message = f"{self.token.position}: Parsing failed, expected "

        if len(self.expected_token_types) > 1:
            message += "one of "

        message += (
            f"{expected}, but found {found}\n" + self.token.position.context() + "\n"
        )
        return message


class EndOfFileException(ParserBaseException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f"{self.file}: Parsing failed, unexpected end of file.\n"


class UnhandledTopLevelToken(ParserBaseException):
    def __init__(self, position: Position, token_type: TokenType) -> None:
        self.position = position
        self.token_type = token_type

    def __str__(self) -> str:  # pragma: nocover
        return (
            f"{self.position}: Parsing failed, unexpected top-level token {self.token_type.name}\n"
            + self.position.context()
            + "\n"
        )

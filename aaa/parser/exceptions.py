from pathlib import Path
from typing import List

from lark.exceptions import UnexpectedInput

from aaa import AaaException
from aaa.tokenizer.models import TokenType


class ParserBaseException(AaaException):
    ...


class ParseException(ParserBaseException):
    # TODO remove once lark is removed
    def __init__(self, *, file: Path, parse_error: UnexpectedInput) -> None:
        self.parse_error = parse_error
        self.file = file

    def where(self) -> str:
        return f"{self.file}:{self.parse_error.line}:{self.parse_error.column}"

    def __str__(self) -> str:
        context = self.parse_error.get_context(self.file.read_text())

        return f"{self.where()}: Could not parse file\n" + context


class FileReadError(ParserBaseException):
    # TODO be sure this is used in NewParser
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f"{self.file}: Failed to open or read\n"


class NewParserException(ParserBaseException):
    def __init__(
        self,
        *,
        file: Path,
        line: int,
        column: int,
        expected_token_types: List[TokenType],
        found_token_type: TokenType,
    ) -> None:
        self.file = file
        self.line = line
        self.column = column
        self.expected_token_types = expected_token_types
        self.found_token_types = found_token_type

    def where(self) -> str:  # pragma: nocover
        return f"{self.file}:{self.line}:{self.column}"

    def context(self) -> str:  # pragma: nocover
        line = self.file.read_text().split("\n")[self.line - 1]
        return line + "\n" + ((self.column - 1) * " ") + "^\n"

    def __str__(self) -> str:  # pragma: nocover
        # TODO confirm this looks right

        expected = ", ".join(
            token_type.name for token_type in self.expected_token_types
        )
        found = self.found_token_types.name

        message = f"{self.where()}: Parsing failed, expected "

        if len(self.expected_token_types) > 1:
            message += "one of "

        message += f"{expected}, but found {found}\n" + self.context() + "\n"
        return message


class NewParserEndOfFileException(ParserBaseException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        # TODO add context
        return f"{self.file} Parsing failed, unexpected end of file."


class NewParserUnhandledTopLevelToken(ParserBaseException):
    def __init__(
        self,
        *,
        file: Path,
        line: int,
        column: int,
        token_type: TokenType,
    ) -> None:
        self.file = file
        self.line = line
        self.column = column
        self.token_type = token_type

    def where(self) -> str:  # pragma: nocover
        return f"{self.file}:{self.line}:{self.column}"

    def context(self) -> str:  # pragma: nocover
        line = self.file.read_text().split("\n")[self.line - 1]
        return line + "\n" + ((self.column - 1) * " ") + "^\n"

    def __str__(self) -> str:  # pragma: nocover
        return (
            f"{self.where()}: Parsing failed, unexpected top-level token {self.token_type.name}\n"
            + self.context()
            + "\n"
        )

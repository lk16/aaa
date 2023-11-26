from pathlib import Path
from typing import List, Set

from aaa.parser.lib.models import Position, Token


class TokenizerException(Exception):
    def __init__(self, position: Position) -> None:
        self.position = position

    def __str__(self) -> str:
        raise NotImplementedError  # TODO


class SyntaxJSONLoadError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return f"Could not load Syntax JSON: {self.msg}"


class ParserBaseException(Exception):
    def __init__(self, offset: int) -> None:
        self.offset = offset


class UnexpectedTokenType(ParserBaseException):
    def __init__(
        self,
        offset: int,
        found_token: Token,
        expected_token_types: str | Set[str],
    ) -> None:
        self.found_token = found_token
        if isinstance(expected_token_types, str):
            self.expected_token_types = {expected_token_types}
        else:
            self.expected_token_types = expected_token_types
        super().__init__(offset)

    def __str__(self) -> str:
        return (
            f"{self.found_token.position}: Unexpected token type\n"
            + "Expected: "
            + ", ".join(sorted(self.expected_token_types))
            + "\n"
            + f"   Found: {self.found_token.type}\n"
        )


class EndOfFile(ParserBaseException):
    def __init__(
        self, file: Path, offset: int, expected_token_types: str | Set[str]
    ) -> None:
        self.file = file
        super().__init__(offset)

        if isinstance(expected_token_types, str):
            self.expected_token_types = {expected_token_types}
        else:
            self.expected_token_types = expected_token_types

    def __str__(self) -> str:
        return (
            f"{self.file}: Parsing failed, unexpected end of file.\n"
            + "Expected: "
            + ", ".join(sorted(self.expected_token_types))
        )


class ChoiceParserException(ParserBaseException):
    def __init__(self, exceptions: List[ParserBaseException]) -> None:
        if len(exceptions) < 2:
            raise ValueError("Need at least two exceptions.")

        flattened_exceptions: List[ParserBaseException] = []

        for exception in exceptions:
            if isinstance(exception, ChoiceParserException):
                flattened_exceptions += exception.exceptions
            else:
                flattened_exceptions.append(exception)

        self.exceptions: List[ParserBaseException] = flattened_exceptions

    def __str__(self) -> str:
        # TODO consider only exceptions with largest offset

        msg = "Parsing failed because all options failed:\n"
        for e in self.exceptions:
            if isinstance(e, UnexpectedTokenType):
                msg += (
                    f"- Unexpected token {e.found_token.type} at offset {e.offset}. Expected one of: "
                    + ", ".join(sorted(e.expected_token_types))
                    + "\n"
                )
            elif isinstance(e, EndOfFile):
                msg += (
                    f"- Unexpected end of file at offset {e.offset}. Expected one of: "
                    + ", ".join(sorted(e.expected_token_types))
                    + "\n"
                )
            else:
                raise NotImplementedError  # Unknown ParserBaseException

        return msg

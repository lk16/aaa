from typing import List, Set

from aaa.parser.lib.models import EndOfFile, Position, Token


class ParseErrorCollector:
    def __init__(self) -> None:
        self.errors: List[ParseError] = []

    def register(self, error: "ParseError") -> None:
        self.errors.append(error)

    def reset(self) -> None:
        self.errors = []

    def get_furthest_error(self) -> "ParseError":
        if not self.errors:
            raise ValueError("No errors were collected.")

        max_offset = -1
        furthest_errors: List[ParseError] = []

        for error in self.errors:
            if error.offset > max_offset:
                max_offset = error.offset
                furthest_errors = [error]
            if error.offset == max_offset:
                furthest_errors.append(error)

        furthest_token = furthest_errors[0].found

        expected_token_types: Set[str] = set()

        for error in furthest_errors:
            expected_token_types.update(error.expected_token_types)

        return ParseError(max_offset, furthest_token, expected_token_types)


class TokenizerException(Exception):
    def __init__(self, position: Position) -> None:
        self.position = position

    def __str__(self) -> str:
        return f"{self.position}: Tokenization failed."


class SyntaxJSONLoadError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return f"Could not load Syntax JSON: {self.msg}"


class ParseError(Exception):
    def __init__(
        self,
        offset: int,
        found: Token | EndOfFile,
        expected_token_types: Set[str],
    ) -> None:
        self.found = found
        self.expected_token_types = expected_token_types
        self.offset = offset

    def __str__(self) -> str:
        if isinstance(self.found, EndOfFile):
            return (
                f"{self.found.file}: Unexpected end of file\n"
                + "Expected one of: "
                + ", ".join(sorted(self.expected_token_types))
                + "\n"
            )

        return (
            f"{self.found.position}: Unexpected token type\n"
            + "Expected one of: "
            + ", ".join(sorted(self.expected_token_types))
            + "\n"
            + f"          Found: {self.found.type}\n"
        )

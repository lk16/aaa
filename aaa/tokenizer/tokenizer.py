from pathlib import Path
from re import Pattern
from typing import List, NoReturn, Optional

from aaa import Position
from aaa.tokenizer.constants import FIXED_SIZED_TOKENS
from aaa.tokenizer.exceptions import FileReadError, TokenizerException
from aaa.tokenizer.models import Token, TokenType
from aaa.tokenizer.regex import (
    character_literal_regex,
    comment_regex,
    identifier_regex,
    integer_regex,
    string_literal_regex,
    whitespace_regex,
)


class Tokenizer:
    def __init__(self, file: Path, verbose: bool) -> None:
        self.file = file
        self.code = ""
        self.verbose = verbose

    def _fail(self, offset: int) -> NoReturn:
        position = self._get_position(offset)
        raise TokenizerException(position)

    def _get_position(self, offset: int) -> Position:
        prefix = self.code[:offset]
        line = 1 + prefix.count("\n")
        column = offset - prefix.rfind("\n")
        return Position(self.file, line, column)

    def _is_fixed_sized_token_boundary(self, offset: int) -> bool:
        try:
            char = self.code[offset]
        except IndexError:
            return True

        return not char.isalpha() and char != "_"

    def _create_token(self, token_type: TokenType, start: int, end: int) -> Token:
        position = self._get_position(start)
        return Token(position, token_type, self.code[start:end])

    def _regex(
        self, offset: int, regex: Pattern[str], token_type: TokenType
    ) -> Optional[Token]:
        match = regex.match(self.code[offset:])

        if not match:
            return None

        end = offset + len(match.group(0))
        return self._create_token(token_type, offset, end)

    def _tokenize_whitespace(self, offset: int) -> Optional[Token]:
        return self._regex(offset, whitespace_regex, TokenType.WHITESPACE)

    def _tokenize_fixed_size(self, offset: int) -> Optional[Token]:
        token: Optional[Token] = None

        for value, token_type in FIXED_SIZED_TOKENS:
            if self.code[offset:].startswith(value):
                end = offset + len(value)

                if not value.isalpha() or self._is_fixed_sized_token_boundary(
                    offset + len(value)
                ):
                    token = self._create_token(token_type, offset, end)
                    break

        return token

    def _tokenize_comment(self, offset: int) -> Optional[Token]:
        return self._regex(offset, comment_regex, TokenType.COMMENT)

    def _tokenize_integer(self, offset: int) -> Optional[Token]:
        return self._regex(offset, integer_regex, TokenType.INTEGER)

    def _tokenize_identifier(self, offset: int) -> Optional[Token]:
        return self._regex(offset, identifier_regex, TokenType.IDENTIFIER)

    def _tokenize_string(self, offset: int) -> Optional[Token]:
        return self._regex(offset, string_literal_regex, TokenType.STRING)

    def _tokenize_character(self, offset: int) -> Optional[Token]:
        return self._regex(offset, character_literal_regex, TokenType.CHARACTER)

    def _print_tokens(self, tokens: List[Token]) -> None:  # pragma: nocover
        if not self.verbose:
            return

        for token in tokens:
            file = token.position.short_filename()
            line = token.position.line
            column = token.position.column
            pos = f"{file}:{line}:{column}"
            print(f"tokenizer | {pos:<30} | {token.type.value:>16} | {token.value}")

    def run(self) -> List[Token]:
        tokens = self.tokenize_unfiltered()

        filtered: List[Token] = []

        for token in tokens:
            if token.type not in [
                TokenType.WHITESPACE,
                TokenType.COMMENT,
            ]:
                filtered.append(token)

        self._print_tokens(filtered)

        return filtered

    def tokenize_unfiltered(self) -> List[Token]:
        try:
            self.code = self.file.read_text()
        except OSError as e:
            raise FileReadError(self.file) from e

        offset = 0
        tokens: List[Token] = []

        while offset < len(self.code):
            token = (
                self._tokenize_whitespace(offset)
                or self._tokenize_comment(offset)
                or self._tokenize_integer(offset)
                or self._tokenize_fixed_size(offset)
                or self._tokenize_string(offset)
                or self._tokenize_identifier(offset)
                or self._tokenize_character(offset)
            )

            if not token:
                self._fail(offset)

            tokens.append(token)
            offset += len(token.value)

        return tokens

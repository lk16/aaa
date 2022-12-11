import re
from pathlib import Path
from typing import List, NoReturn, Optional, Tuple

from aaa.tokenizer.constants import (
    FIXED_SIZED_TOKENS,
    ONE_CHAR_PREFIXED_SIZED_TOKENS,
    TWO_CHAR_PREFIXED_SIZED_TOKENS,
)
from aaa.tokenizer.exceptions import FileReadError, TokenizerException
from aaa.tokenizer.models import Token, TokenType

comment_regex = re.compile("//[^\n]*")
shebang_regex = re.compile("#![^\n]*")
integer_regex = re.compile("(-)?[0-9]+")
identifier_regex = re.compile("[a-zA-Z_]+")

IDENTIFIER_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"


class Tokenizer:
    def __init__(self, file: Path) -> None:
        self.file = file
        self.code = ""

    def _fail(self, offset: int) -> NoReturn:
        line, column = self._get_line_col(offset)
        raise TokenizerException(self.file, line, column)

    def _get_line_col(self, offset: int) -> Tuple[int, int]:
        prefix = self.code[:offset]
        line = 1 + prefix.count("\n")
        column = offset - prefix.rfind("\n")
        return line, column

    def _create_token(self, token_type: TokenType, start: int, end: int) -> Token:
        line, column = self._get_line_col(start)

        return Token(
            token_type,
            value=self.code[start:end],
            file=self.file,
            line=line,
            column=column,
        )

    def _regex(
        self, offset: int, pattern: re.Pattern[str], token_type: TokenType
    ) -> Optional[Token]:
        match = pattern.match(self.code[offset:])

        if not match:
            return None

        end = offset + len(match.group(0))
        return self._create_token(token_type, offset, end)

    def _tokenize_whitespace(self, offset: int) -> Optional[Token]:
        ws_len = 0

        while True:
            end = offset + ws_len

            if end >= len(self.code):
                break

            if not self.code[offset + ws_len].isspace():
                break

            ws_len += 1

        if ws_len == 0:
            return None

        return self._create_token(TokenType.WHITESPACE, offset, offset + ws_len)

    def _tokenize_fixed_size(self, offset: int) -> Optional[Token]:
        token: Optional[Token] = None

        try:
            token_type = ONE_CHAR_PREFIXED_SIZED_TOKENS[self.code[offset]]
        except KeyError:
            pass
        else:
            return self._create_token(token_type, offset, offset + 1)

        try:
            remainder, token_type = TWO_CHAR_PREFIXED_SIZED_TOKENS[
                self.code[offset : offset + 2]
            ]
        except KeyError:
            pass
        else:
            if remainder and not self.code[offset + 2 :].startswith(remainder):
                return None

            length = 2 + len(remainder)

            if (
                offset + length < len(self.code)
                and self.code[offset + length] in IDENTIFIER_CHARS
            ):
                return None

            return self._create_token(token_type, offset, offset + length)

        for value, token_type in FIXED_SIZED_TOKENS:
            if self.code[offset:].startswith(value):
                end = offset + len(value)

                if (
                    end >= len(self.code)
                    or self.code[end].isspace()
                    or not value.isalpha()
                ):
                    found = self._create_token(token_type, offset, end)

                    # keep longest token
                    if not token or (len(found.value) > len(token.value)):
                        token = found

        return token

    def _tokenize_comment(self, offset: int) -> Optional[Token]:
        if not self.code[offset:].startswith("//"):
            return None

        return self._regex(offset, comment_regex, TokenType.COMMENT)

    def _tokenize_shebang(self, offset: int) -> Optional[Token]:
        if not self.code[offset:].startswith("#!"):
            return None

        return self._regex(offset, shebang_regex, TokenType.SHEBANG)

    def _tokenize_integer(self, offset: int) -> Optional[Token]:
        if self.code[offset] not in "-0123456789":
            return None

        return self._regex(offset, integer_regex, TokenType.INTEGER)

    def _tokenize_identifier(self, offset: int) -> Optional[Token]:
        if self.code[offset] not in IDENTIFIER_CHARS:
            return None

        return self._regex(offset, identifier_regex, TokenType.IDENTIFIER)

    def _tokenize_string(self, offset: int) -> Optional[Token]:
        if self.code[offset] != '"':
            return None

        start = offset
        offset = start + 1

        while True:
            if offset >= len(self.code):
                self._fail(start)

            if not self.code[offset].isprintable():
                self._fail(start)

            if self.code[offset] == '"':
                return self._create_token(TokenType.STRING, start, offset + 1)

            if self.code[offset] == "\\":

                try:
                    escaped = self.code[offset + 1]
                except IndexError:
                    self._fail(start)

                if escaped not in ["n", "r", "\\", '"']:
                    self._fail(start)

                offset += 2
            else:
                offset += 1

    def run(self) -> List[Token]:
        # TODO catch TokenizerException
        # TODO return model with tokens and exceptions

        tokens = self.tokenize_unfiltered()

        filtered: List[Token] = []

        for token in tokens:
            if token.type not in [
                TokenType.WHITESPACE,
                TokenType.COMMENT,
                TokenType.SHEBANG,
            ]:
                filtered.append(token)

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
                or self._tokenize_shebang(offset)
                or self._tokenize_integer(offset)
                or self._tokenize_fixed_size(offset)
                or self._tokenize_string(offset)
                or self._tokenize_identifier(offset)
            )

            if not token:
                self._fail(offset)

            tokens.append(token)
            offset += len(token.value)

        return tokens

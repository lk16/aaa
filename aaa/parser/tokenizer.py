import re
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple


class TokenType(Enum):
    ARGS = "ARGS"
    AS = "AS"
    BEGIN = "BEGIN"
    COMMA = "COMMA"
    COLON = "COLON"
    COMMENT = "COMMENT"
    ELSE = "ELSE"
    END = "END"
    FALSE = "FALSE"
    FROM = "FROM"
    FUNCTION = "FUNCTION"
    GET_FIELD = "GET_FIELD"
    IDENTIFIER = "IDENTIFIER"
    IF = "IF"
    INTEGER = "INTEGER"
    IMPORT = "IMPORT"
    OPERATOR = "OPERATOR"
    RETURN = "RETURN"
    SET_FIELD = "SET_FIELD"
    SHEBANG = "SHEBANG"
    STRING = "STRING"
    STRUCT = "STRUCT"
    TRUE = "TRUE"
    TYPE = "TYPE"
    TYPE_PARAM_BEGIN = "TYPE_PARAM_BEGIN"
    TYPE_PARAM_END = "TYPE_PARAM_END"
    WHILE = "WHILE"
    WHITESPACE = "WHITESPACE"


class Token:
    def __init__(
        self, type: TokenType, value: str, file: Path, line: int, column: int
    ) -> None:
        self.type = type
        self.value = value
        self.file = file
        self.line = line
        self.column = column

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.type}, value={repr(self.value)})"


FIXED_SIZED_TOKENS: List[Tuple[str, TokenType]] = [
    ("-", TokenType.OPERATOR),
    (",", TokenType.COMMA),
    ("!", TokenType.SET_FIELD),
    ("!=", TokenType.OPERATOR),
    ("?", TokenType.GET_FIELD),
    (".", TokenType.OPERATOR),
    ("[", TokenType.TYPE_PARAM_BEGIN),
    ("]", TokenType.TYPE_PARAM_END),
    ("{", TokenType.BEGIN),
    ("}", TokenType.END),
    ("*", TokenType.OPERATOR),
    ("/", TokenType.OPERATOR),
    ("%", TokenType.OPERATOR),
    ("+", TokenType.OPERATOR),
    ("<", TokenType.OPERATOR),
    ("<=", TokenType.OPERATOR),
    ("=", TokenType.OPERATOR),
    (">", TokenType.OPERATOR),
    (">=", TokenType.OPERATOR),
    (":", TokenType.COLON),
    ("args", TokenType.ARGS),
    ("as", TokenType.AS),
    ("else", TokenType.ELSE),
    ("false", TokenType.FALSE),
    ("fn", TokenType.FUNCTION),
    ("from", TokenType.FROM),
    ("if", TokenType.IF),
    ("import", TokenType.IMPORT),
    ("return", TokenType.RETURN),
    ("struct", TokenType.STRUCT),
    ("true", TokenType.TRUE),
    ("type", TokenType.TYPE),
    ("while", TokenType.WHILE),
]


class Tokenizer:
    def __init__(self, file: Path) -> None:
        self.file = file
        self.code = file.read_text()

    def _create_token(self, token_type: TokenType, start: int, end: int) -> Token:
        # TODO compute line, column
        line = 1 + self.code[:start].count("\n")
        column = start - self.code[:start].rfind("\n")
        return Token(
            token_type,
            value=self.code[start:end],
            file=self.file,
            line=line,
            column=column,
        )

    def _regex(self, offset: int, regex: str, token_type: TokenType) -> Optional[Token]:
        match = re.match(regex, self.code[offset:])

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
        return self._regex(offset, "//[^\n]*", TokenType.COMMENT)

    def _tokenize_shebang(self, offset: int) -> Optional[Token]:
        return self._regex(offset, "#![^\n]*", TokenType.SHEBANG)

    def _tokenize_integer(self, offset: int) -> Optional[Token]:
        return self._regex(offset, "(-)?[0-9]+", TokenType.INTEGER)

    def _tokenize_identifier(self, offset: int) -> Optional[Token]:
        return self._regex(offset, "[a-zA-Z_]+", TokenType.IDENTIFIER)

    def _tokenize_string(self, offset: int) -> Optional[Token]:
        if self.code[offset] != '"':
            return None

        start = offset
        offset = start + 1

        while True:
            if offset > len(self.code):
                # File ended
                # TODO raise some string parsing error
                return None

            if not self.code[offset].isprintable():
                # Unprintable character (includes newline)
                # TODO raise some string parsing error
                return None

            if self.code[offset] == '"':
                return self._create_token(TokenType.STRING, start, offset + 1)

            if self.code[offset] == "\\":
                # TODO check if escape sequence is valid, if not raise some string parsing error
                offset += 2
            else:
                offset += 1

    def run(self) -> List[Token]:
        tokens = self.tokenize_unfiltered()

        filtered: List[Token] = []

        for token in tokens:
            if token.type not in [TokenType.WHITESPACE, TokenType.COMMENT]:
                filtered.append(token)

        return filtered

    def tokenize_unfiltered(self) -> List[Token]:
        offset = 0
        tokens: List[Token] = []

        while offset < len(self.code):
            token = (
                self._tokenize_whitespace(offset)
                or self._tokenize_comment(offset)
                or self._tokenize_shebang(offset)
                or self._tokenize_fixed_size(offset)
                or self._tokenize_integer(offset)
                or self._tokenize_string(offset)
                or self._tokenize_identifier(offset)
            )

            if not token:
                # TODO raise exception
                print(
                    "Tokenize error, next few characters: ",
                    self.code[offset : offset + 20],
                )
                exit()

            if token.type != TokenType.WHITESPACE:
                print(
                    f"{token.line:>4}:{token.column:>3} {token.type.value:>20} {repr(token.value)}"
                )

            tokens.append(token)
            offset += len(token.value)

        return tokens

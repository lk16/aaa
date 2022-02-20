from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Final, List, Optional, Set, Tuple

from lang.exceptions import (
    InvalidStringEscapeSequence,
    TokenizeError,
    UnterminatedStringError,
)


# TODO reduce number of TokenTypes by grouping operators, built-in functions and so on
class TokenType(IntEnum):
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    TRUE = auto()
    FALSE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    EQUAL = auto()
    GREATER_THAN = auto()
    GREATER_EQUAL = auto()
    LESS_THAN = auto()
    LESS_EQUAL = auto()
    NOT_EQUAL = auto()
    DROP = auto()
    DUPLICATE = auto()
    SWAP = auto()
    OVER = auto()
    ROTATE = auto()
    PRINT_NEWLINE = auto()
    PRINT = auto()
    IF = auto()
    ELSE = auto()
    END = auto()
    WHILE = auto()
    INTEGER = auto()
    UNHANDLED = auto()  # For testing purposes
    STRING = auto()
    SUBSTRING = auto()
    COMMENT = auto()
    STRING_LENGTH = auto()
    FUNCTION = auto()
    FUNCTION_BEGIN = auto()
    IDENTIFIER = auto()


# TODO change in to dict again and lookup directly in Tokenizer.try_tokenize_simple()
SIMPLE_TOKENS: Final[List[Tuple[str, TokenType]]] = [
    ("+", TokenType.PLUS),
    ("-", TokenType.MINUS),
    ("*", TokenType.STAR),
    ("/", TokenType.SLASH),
    ("%", TokenType.PERCENT),
    ("true", TokenType.TRUE),
    ("false", TokenType.FALSE),
    ("and", TokenType.AND),
    ("or", TokenType.OR),
    ("not", TokenType.NOT),
    ("=", TokenType.EQUAL),
    (">", TokenType.GREATER_THAN),
    (">=", TokenType.GREATER_EQUAL),
    ("<", TokenType.LESS_THAN),
    ("<=", TokenType.LESS_EQUAL),
    ("!=", TokenType.NOT_EQUAL),
    ("drop", TokenType.DROP),
    ("dup", TokenType.DUPLICATE),
    ("swap", TokenType.SWAP),
    ("over", TokenType.OVER),
    ("rot", TokenType.ROTATE),
    ("\\n", TokenType.PRINT_NEWLINE),
    (".", TokenType.PRINT),
    ("if", TokenType.IF),
    ("else", TokenType.ELSE),
    ("end", TokenType.END),
    ("while", TokenType.WHILE),
    ("substr", TokenType.SUBSTRING),
    ("strlen", TokenType.STRING_LENGTH),
    ("fn", TokenType.FUNCTION),
    ("begin", TokenType.FUNCTION_BEGIN),
]

SIMPLE_TOKEN_TYPES: Final[Set[TokenType]] = {item[1] for item in SIMPLE_TOKENS}
NON_SIMPLE_TOKEN_TYPES: Final[Set[TokenType]] = (
    set(TokenType) - SIMPLE_TOKEN_TYPES - {TokenType.UNHANDLED}
)


@dataclass
class Token:
    filename: str
    line_number: int
    offset: int
    value: str
    type: TokenType


def tokenize(code: str, filename: str) -> List[Token]:
    return Tokenizer(code, filename).run()


class Tokenizer:
    def __init__(self, code: str, filename: str) -> None:
        self.code = code
        self.filename = filename
        self.offset = 0
        self.line = ""

    def try_tokenize_simple(self) -> Optional[Token]:
        line_part = self.line[self.offset :]

        for token_str, token_type in SIMPLE_TOKENS:
            # Force a space after the matched simple token
            # This rules out problems like mismatching <= with LESS_THAN instead of LESS_EQUAL
            if (line_part + " ").startswith(token_str + " "):
                return Token(
                    self.filename,
                    self.line_number,
                    self.offset,
                    token_str,
                    token_type,
                )

        return None

    def try_tokenize_integer(self) -> Optional[Token]:
        length = 0
        for i in range(self.offset, len(self.line)):
            if self.line[i].isdigit():
                length += 1
            else:
                break

        if length == 0:
            return None

        return Token(
            self.filename,
            self.line_number,
            self.offset,
            self.line[self.offset : self.offset + length],
            TokenType.INTEGER,
        )

    def try_tokenize_string(self) -> Optional[Token]:

        if self.line[self.offset] != '"':
            return None

        i = self.offset + 1
        while i < len(self.line):
            char = self.line[i]

            if char == '"':
                return Token(
                    self.filename,
                    self.line_number,
                    self.offset,
                    self.line[self.offset : i + 1],
                    TokenType.STRING,
                )

            if char == "\\":
                try:
                    next_char = self.line[i + 1]
                except IndexError:
                    raise UnterminatedStringError(
                        self.filename, self.line_number, self.offset, self.line
                    )

                if next_char not in ["\\", '"', "n"]:
                    raise InvalidStringEscapeSequence(
                        self.filename, self.line_number, self.offset, self.line
                    )

                i += 2

            else:
                i += 1

        raise UnterminatedStringError(
            self.filename, self.line_number, self.offset, self.line
        )

    def try_tokenize_identifier(self) -> Optional[Token]:
        space_offset = (self.line[self.offset :] + " ").find(" ")
        identifier = self.line[self.offset : self.offset + space_offset]
        identifier_chars = set(identifier)

        if identifier_chars.issubset("abcdefghijklmnopqrstuvwxyz_"):
            return Token(
                self.filename,
                self.line_number,
                self.offset,
                identifier,
                TokenType.IDENTIFIER,
            )

        return None

    def try_tokenize_comment(self) -> Optional[Token]:
        if self.line[self.offset : self.offset + 2] == "//":
            token = Token(
                self.filename,
                self.line_number,
                self.offset,
                self.line[self.offset :],
                TokenType.COMMENT,
            )
            return token
        return None

    def skip_whitespace(self) -> None:
        line_remainder = self.line[self.offset :]
        self.offset += len(line_remainder) - len(line_remainder.lstrip())

    def tokenize_line(self) -> List[Token]:
        try_tokenize_funcs = [
            self.try_tokenize_simple,
            self.try_tokenize_comment,
            self.try_tokenize_string,
            self.try_tokenize_integer,
            self.try_tokenize_identifier,
        ]

        tokens: List[Token] = []
        self.offset = 0

        self.skip_whitespace()

        while self.offset < len(self.line):

            token: Optional[Token] = None

            for try_tokenize_func in try_tokenize_funcs:
                token = try_tokenize_func()

                if token:
                    break

            if token:
                tokens.append(token)
                self.offset += len(token.value)
                self.skip_whitespace()

            else:
                raise TokenizeError(
                    self.filename, self.line_number, self.offset, self.line
                )

        return tokens

    def run(self) -> List[Token]:
        tokens: List[Token] = []

        for line_number, line in enumerate(self.code.split("\n"), start=1):
            self.line = line
            self.line_number = line_number
            tokens += self.tokenize_line()

        return tokens

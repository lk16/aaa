from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Dict, List, Optional

from lang.exceptions import TokenizeError


class TokenType(IntEnum):
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
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


simple_tokens: Dict[str, TokenType] = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "=": TokenType.EQUAL,
    ">": TokenType.GREATER_THAN,
    ">=": TokenType.GREATER_EQUAL,
    "<": TokenType.LESS_THAN,
    "<=": TokenType.LESS_EQUAL,
    "!=": TokenType.NOT_EQUAL,
    "drop": TokenType.DROP,
    "dup": TokenType.DUPLICATE,
    "swap": TokenType.SWAP,
    "over": TokenType.OVER,
    "rot": TokenType.ROTATE,
    "\\n": TokenType.PRINT_NEWLINE,
    ".": TokenType.PRINT,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "end": TokenType.END,
    "while": TokenType.WHILE,
}


@dataclass
class Token:
    file_name: str
    line_number: int
    offset: int
    length: int
    type: TokenType


class Tokenizer:
    def __init__(self, code: str, filename: str) -> None:
        self.code = code
        self.filename = filename
        self.offset = 0
        self.line = ""

    def try_tokenize_simple(self) -> Optional[Token]:
        line_part = self.line[self.offset :]

        for token_str, token_type in simple_tokens.items():
            if line_part.startswith(token_str):
                return Token(
                    self.filename,
                    self.line_number,
                    self.offset,
                    len(token_str),
                    token_type,
                )
        return None

    def tokenize_integer(self) -> Token:
        length = 0
        for i in range(self.offset, len(self.line)):
            if self.line[i].isdigit():
                length += 1
            else:
                break

        return Token(
            self.filename,
            self.line_number,
            self.offset,
            length,
            TokenType.INTEGER,
        )

    def tokenize_line(self) -> List[Token]:
        self.offset = 0
        tokens = []

        while self.offset < len(self.line):
            if self.line[self.offset] == " ":
                self.offset += 1
                continue

            token = self.try_tokenize_simple()
            if token:
                tokens.append(token)
                self.offset += token.length
                continue

            if self.line[self.offset].isdigit():
                token = self.tokenize_integer()
                tokens.append(token)
                self.offset += token.length
                continue

            raise TokenizeError(self.filename, self.line_number, self.offset, self.line)

        return tokens

    def run(self) -> List[Token]:
        tokens: List[Token] = []

        for line_number, line in enumerate(self.code.split("\n"), start=1):
            self.line = line
            self.line_number = line_number
            tokens += self.tokenize_line()

        return tokens

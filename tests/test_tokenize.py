from typing import List, Type

import pytest

from lang.exceptions import (
    InvalidStringEscapeSequence,
    TokenizeError,
    UnterminatedStringError,
)
from lang.tokenize import TokenType, tokenize


@pytest.mark.parametrize(
    ["code", "expected_token_types"],
    [
        ("", []),
        ("+", [TokenType.PLUS]),
        ("-", [TokenType.MINUS]),
        ("*", [TokenType.STAR]),
        ("/", [TokenType.SLASH]),
        ("true", [TokenType.TRUE]),
        ("false", [TokenType.FALSE]),
        ("and", [TokenType.AND]),
        ("or", [TokenType.OR]),
        ("not", [TokenType.NOT]),
        ("=", [TokenType.EQUAL]),
        (">", [TokenType.GREATER_THAN]),
        (">=", [TokenType.GREATER_EQUAL]),
        ("<", [TokenType.LESS_THAN]),
        ("<=", [TokenType.LESS_EQUAL]),
        ("!=", [TokenType.NOT_EQUAL]),
        ("drop", [TokenType.DROP]),
        ("dup", [TokenType.DUPLICATE]),
        ("swap", [TokenType.SWAP]),
        ("over", [TokenType.OVER]),
        ("rot", [TokenType.ROTATE]),
        ("\\n", [TokenType.PRINT_NEWLINE]),
        (".", [TokenType.PRINT]),
        ("if", [TokenType.IF]),
        ("else", [TokenType.ELSE]),
        ("end", [TokenType.END]),
        ("while", [TokenType.WHILE]),
        ("1", [TokenType.INTEGER]),
        ("1234567", [TokenType.INTEGER]),
        ("truetrue", [TokenType.TRUE, TokenType.TRUE]),
        ("1+1", [TokenType.INTEGER, TokenType.PLUS, TokenType.INTEGER]),
        (
            "trueif123.end",
            [
                TokenType.TRUE,
                TokenType.IF,
                TokenType.INTEGER,
                TokenType.PRINT,
                TokenType.END,
            ],
        ),
    ],
)
def test_tokenize_ok(code: str, expected_token_types: List[TokenType]) -> None:
    tokens = tokenize(code, "<stdin>")
    token_types = [token.type for token in tokens]
    assert expected_token_types == token_types


@pytest.mark.parametrize(
    ["code", "expected_exception"],
    [
        ("adsfasdf", TokenizeError),
        ('"', UnterminatedStringError),
        ('"\\"', UnterminatedStringError),
        ('"\\', UnterminatedStringError),
        ('"\\x"', InvalidStringEscapeSequence),
    ],
)
def test_tokenize_fail(code: str, expected_exception: Type[Exception]) -> None:
    with pytest.raises(expected_exception):
        tokenize(code, "<stdin>")

from typing import List, Type

import pytest

from lang.exceptions import InvalidStringEscapeSequence, UnterminatedStringError
from lang.tokenize import SIMPLE_TOKENS, TokenType, tokenize


@pytest.mark.parametrize(
    ["code", "expected_token_types"],
    [(token_str, [token_type]) for (token_str, token_type) in SIMPLE_TOKENS]
    + [
        ("1", [TokenType.INTEGER]),
        ("1234567", [TokenType.INTEGER]),
        ("//", [TokenType.COMMENT]),
        ("// adsfasdf", [TokenType.COMMENT]),
        ("a", [TokenType.IDENTIFIER]),
        ("aaaaa", [TokenType.IDENTIFIER]),
        ("the_quick_brown_fox_jumps_over_the_lazy_dog", [TokenType.IDENTIFIER]),
    ],
)
def test_tokenize_ok(code: str, expected_token_types: List[TokenType]) -> None:
    tokens = tokenize(code, "<stdin>")
    token_types = [token.type for token in tokens]
    assert expected_token_types == token_types


@pytest.mark.parametrize(
    ["code", "expected_exception"],
    [
        ('"', UnterminatedStringError),
        ('"\\"', UnterminatedStringError),
        ('"\\', UnterminatedStringError),
        ('"\\x"', InvalidStringEscapeSequence),
    ],
)
def test_tokenize_fail(code: str, expected_exception: Type[Exception]) -> None:
    with pytest.raises(expected_exception):
        tokenize(code, "<stdin>")

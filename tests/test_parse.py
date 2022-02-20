from typing import List, Type

import pytest

from lang.exceptions import BlockStackNotEmpty, UnexpectedToken, UnhandledTokenType
from lang.parse import parse
from lang.tokenize import Token, TokenType


def token(token_type: TokenType, value: str = "") -> Token:
    return Token("<stdin>", 0, 0, value, token_type)


@pytest.mark.parametrize(
    ["tokens", "expected_exception"],
    [
        ([token(TokenType.ELSE)], UnexpectedToken),
        ([token(TokenType.END)], UnexpectedToken),
        ([token(TokenType.UNHANDLED)], UnhandledTokenType),
        ([token(TokenType.IF)], BlockStackNotEmpty),
        ([token(TokenType.IF), token(TokenType.ELSE)], BlockStackNotEmpty),
        ([token(TokenType.WHILE)], BlockStackNotEmpty),
    ],
)
def test_parse_fail(tokens: List[Token], expected_exception: Type[Exception]) -> None:
    with pytest.raises(expected_exception):
        parse(tokens)

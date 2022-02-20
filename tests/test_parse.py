from typing import List, Type

import pytest

from lang.exceptions import UnexpectedEndOfFile, UnexpectedToken, UnhandledTokenType
from lang.parse import parse
from lang.tokenize import Token, TokenType


def token(token_type: TokenType) -> Token:
    return Token("<stdin>", 0, 0, "", token_type)


@pytest.mark.parametrize(
    ["tokens", "expected_exception"],
    [
        (
            [
                token(TokenType.FUNCTION),
                token(TokenType.IDENTIFIER),
                token(TokenType.FUNCTION_BEGIN),
                token(TokenType.ELSE),
            ],
            UnexpectedToken,
        ),
        (
            [
                token(TokenType.FUNCTION),
                token(TokenType.IDENTIFIER),
                token(TokenType.FUNCTION_BEGIN),
                token(TokenType.UNHANDLED),
            ],
            UnhandledTokenType,
        ),
        (
            [
                token(TokenType.FUNCTION),
                token(TokenType.IDENTIFIER),
                token(TokenType.FUNCTION_BEGIN),
                token(TokenType.IF),
            ],
            UnexpectedEndOfFile,
        ),
        (
            [
                token(TokenType.FUNCTION),
                token(TokenType.IDENTIFIER),
                token(TokenType.FUNCTION_BEGIN),
                token(TokenType.IF),
                token(TokenType.ELSE),
            ],
            UnexpectedEndOfFile,
        ),
        (
            [
                token(TokenType.FUNCTION),
                token(TokenType.IDENTIFIER),
                token(TokenType.FUNCTION_BEGIN),
                token(TokenType.WHILE),
            ],
            UnexpectedEndOfFile,
        ),
    ],
)
def test_parse_fail(tokens: List[Token], expected_exception: Type[Exception]) -> None:
    with pytest.raises(expected_exception):
        parse(tokens)

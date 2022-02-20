from typing import List, Type

import pytest

from lang.exceptions import (
    NoMainFunctionFound,
    UnexpectedEndOfFile,
    UnexpectedToken,
    UnhandledTokenType,
)
from lang.parse import parse
from lang.program import Program
from lang.tokenize import Token, TokenType
from lang.types import Function


def token(token_type: TokenType, value: str = "") -> Token:
    return Token("<stdin>", 0, 0, value, token_type)


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
        (
            [token(TokenType.INTEGER)],
            UnexpectedToken,
        ),
        (
            [
                token(TokenType.FUNCTION),
                token(TokenType.AND),
            ],
            UnexpectedToken,
        ),
        ([], NoMainFunctionFound),
        (
            [
                token(TokenType.FUNCTION),
                token(TokenType.IDENTIFIER),
                token(TokenType.AND),
                token(TokenType.FUNCTION_BEGIN),
                token(TokenType.WHILE),
            ],
            UnexpectedToken,
        ),
    ],
)
def test_parse_fail(tokens: List[Token], expected_exception: Type[Exception]) -> None:
    with pytest.raises(expected_exception):
        parse(tokens)


@pytest.mark.parametrize(
    ["tokens", "expected_program"],
    [
        (
            [
                token(TokenType.COMMENT),
                token(TokenType.FUNCTION),
                token(TokenType.IDENTIFIER, value="main"),
                token(TokenType.FUNCTION_BEGIN),
                token(TokenType.END),
            ],
            Program({"main": Function("main", 0, [])}),
        ),
        (
            [
                token(TokenType.FUNCTION),
                token(TokenType.IDENTIFIER, value="main"),
                token(TokenType.IDENTIFIER, value="foo"),
                token(TokenType.FUNCTION_BEGIN),
                token(TokenType.END),
            ],
            Program({"main": Function("main", 1, [])}),
        ),
    ],
)
def test_parse_ok(tokens: List[Token], expected_program: Program) -> None:
    program = parse(tokens)
    assert vars(expected_program) == vars(program)

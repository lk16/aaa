from typing import List

import pytest

from lang.exceptions import BlockStackNotEmpty, SyntaxException, UnexpectedOperation
from lang.operations import (
    And,
    BoolPush,
    Divide,
    Else,
    End,
    If,
    IntPush,
    Minus,
    Multiply,
    Not,
    Operation,
    Or,
    Plus,
    Print,
)
from lang.parse import parse


@pytest.mark.parametrize(
    ["code", "expected_operations"],
    [
        ("", []),
        ("1", [IntPush(1)]),
        ("1 1", [IntPush(1), IntPush(1)]),
        ("11", [IntPush(11)]),
        ("123456789", [IntPush(123456789)]),
        ("+", [Plus()]),
        ("-", [Minus()]),
        ("*", [Multiply()]),
        ("/", [Divide()]),
        ("true", [BoolPush(True)]),
        ("false", [BoolPush(False)]),
        ("and", [And()]),
        ("or", [Or()]),
        ("not", [Not()]),
        (".", [Print()]),
        ("if end", [If(1), End()]),
        ("if if end end", [If(3), If(2), End(), End()]),
    ],
)
def test_parse_ok(code: str, expected_operations: List[Operation]) -> None:
    assert expected_operations == parse(code)


@pytest.mark.parametrize(
    ["code", "expected_exception"],
    [
        (
            "unexpectedthing",
            SyntaxException("unexpectedthing"),
        ),
        ("-1", SyntaxException("-1")),
        ("if", BlockStackNotEmpty()),
        ("else", UnexpectedOperation(Else(None))),
        ("end", UnexpectedOperation(End())),
    ],
)
def test_parse_fail(code: str, expected_exception: Exception) -> None:
    with pytest.raises(type(expected_exception)) as e:
        parse(code)

    expected_exception.args == e.value.args

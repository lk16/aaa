from typing import List

import pytest

from lang.exceptions import ParseError
from lang.operations import (
    And,
    BoolPrint,
    BoolPush,
    Divide,
    IntPrint,
    IntPush,
    Minus,
    Multiply,
    Not,
    Operation,
    Or,
    Plus,
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
        ("int_print", [IntPrint()]),
        ("+", [Plus()]),
        ("-", [Minus()]),
        ("*", [Multiply()]),
        ("/", [Divide()]),
        ("true", [BoolPush(True)]),
        ("false", [BoolPush(False)]),
        ("and", [And()]),
        ("or", [Or()]),
        ("not", [Not()]),
        ("bool_print", [BoolPrint()]),
    ],
)
def test_parse_ok(code: str, expected_operations: List[Operation]) -> None:
    assert expected_operations == parse(code)


@pytest.mark.parametrize(
    ["code", "expected_exception"],
    [
        (
            "unexpectedthing",
            ParseError(f"Syntax error: can't handle 'unexpectedthing'"),
        ),
        ("-1", ParseError(f"Syntax error: can't handle '-1'")),
    ],
)
def test_parse_fail(code: str, expected_exception: Exception) -> None:
    with pytest.raises(type(expected_exception)) as e:
        parse(code)

    expected_exception.args == e.value.args

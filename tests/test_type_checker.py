from contextlib import nullcontext as does_not_raise
from typing import Optional, Type

import pytest
from _pytest.python_api import RaisesContext

from lang.parse import parse
from lang.typing.checker import TypeChecker
from lang.typing.exceptions import (
    FunctionTypeError,
    StackTypesError,
    StackUnderflowError,
)


@pytest.mark.parametrize(
    ["code", "expected_exception"],
    [
        ("fn foo begin nop end", None),
        ("fn foo begin drop end", StackUnderflowError),
        ("fn foo begin 3 end", FunctionTypeError),
        ("fn foo begin 3 drop end", None),
        ('fn foo begin "a" "b" - end', StackTypesError),
        ('fn foo begin "a" 3 - end', StackTypesError),
        ("fn foo args a as int begin nop end", None),
        ("fn foo return int begin 5 end", None),
        ("fn foo return bool begin 5 end", FunctionTypeError),
        ('fn foo return int, str begin 5 "foo" end', None),
        ('fn foo return str, int begin 5 "foo" end', FunctionTypeError),
        ("fn foo return int, int begin 5 dup end", None),
        ("fn foo return bool, int, bool begin true 5 over end", None),
    ],
)
def test_type_checker(code: str, expected_exception: Optional[Type[Exception]]) -> None:
    root = parse("foo.txt", code)
    function = root.functions["foo"]

    expectation: does_not_raise[None] | RaisesContext[Exception]
    if expected_exception:
        expectation = pytest.raises(expected_exception)
    else:
        expectation = does_not_raise()

    with expectation:
        TypeChecker(function).check()

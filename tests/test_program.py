from contextlib import nullcontext as does_not_raise
from typing import Optional, Type

import pytest
from _pytest.python_api import RaisesContext

from lang.program import Program
from lang.typing.exceptions import (
    FunctionTypeError,
    StackTypesError,
    StackUnderflowError,
    UnknownPlaceholderTypes,
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
        ("fn foo return int begin 5 end", None),
        ("fn foo return bool begin 5 end", FunctionTypeError),
        ('fn foo return int, str begin 5 "foo" end', None),
        ('fn foo return str, int begin 5 "foo" end', FunctionTypeError),
        ("fn foo return int, int begin 5 dup end", None),
        ("fn foo return bool, int, bool begin true 5 over end", None),
        ("fn foo begin 5 5 = drop end", None),
        ('fn foo begin "" "" = drop end', None),
        ("fn foo begin if true begin nop end end", None),
        ("fn foo begin if 3 begin nop end end", StackTypesError),
        ("fn foo begin if true begin nop else nop end end", None),
        ("fn foo begin if true begin 3 else nop end end", StackTypesError),
        ("fn foo begin if true begin nop else 3 end end", StackTypesError),
        ("fn foo begin if true begin 3 end end", StackTypesError),
        ("fn foo begin if 3 2 < begin nop end end", None),
        ("fn foo begin 3 2 if < begin nop end end", StackTypesError),
        ("fn foo begin 3 2 if over over < begin nop end drop drop end", None),
        ("fn foo begin if true true begin nop end end", StackTypesError),
        ("fn foo begin true if dup begin nop end drop end", None),
        ("fn foo begin 3 if drop 2 true begin nop end drop end", None),
        ('fn foo begin 3 if drop "" true begin nop end drop end', StackTypesError),
        ("fn foo begin while true begin nop end end", None),
        ("fn foo begin while true true begin nop end end", StackTypesError),
        ("fn foo begin while 3 2 < begin nop end end", None),
        ("fn foo begin 3 2 while < begin nop end end", StackTypesError),
        ("fn foo begin 3 2 while over over < begin nop end drop drop end", None),
        ("fn foo begin while true begin 3 end end", StackTypesError),
        ("fn foo begin while true begin 3 drop end end", None),
        ("fn foo args a as int begin a a - . end", None),
        ("fn foo args a as int begin a a + . end", None),
        ("fn foo args *a begin nop end", None),
        ("fn foo args *a return *a, *a begin a a end", None),
        ("fn foo args *a return *b begin a end", UnknownPlaceholderTypes),
        ("fn five return int begin 5 end fn foo return int begin five end", None),
        ("fn foo return int begin foo end", None),
        # TODO arguments
        # TODO function calls
    ],
)
def test_type_checker(code: str, expected_exception: Optional[Type[Exception]]) -> None:
    expectation: does_not_raise[None] | RaisesContext[Exception]
    if expected_exception:
        expectation = pytest.raises(expected_exception)
    else:
        expectation = does_not_raise()

    with expectation:
        Program.without_file(code)

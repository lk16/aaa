from parser.parser.exceptions import ParseError
from typing import Optional, Type

import pytest

from lang.runtime.program import Program
from lang.typing.exceptions import (
    ArgumentNameCollision,
    BranchTypeError,
    ConditionTypeError,
    FunctionNameCollision,
    FunctionTypeError,
    LoopTypeError,
    StackTypesError,
    StackUnderflowError,
    UnknownFunction,
    UnknownPlaceholderType,
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
        ("fn foo begin if 3 begin nop end end", ConditionTypeError),
        ("fn foo begin if 3 true begin nop end end", ConditionTypeError),
        ("fn foo begin if true begin nop else nop end end", None),
        ("fn foo begin if true begin 3 else nop end end", BranchTypeError),
        ("fn foo begin if true begin nop else 3 end end", BranchTypeError),
        ("fn foo begin if true begin 3 end end", BranchTypeError),
        ("fn foo begin if 3 2 < begin nop end end", None),
        ("fn foo begin 3 2 if < begin nop end end", ConditionTypeError),
        ("fn foo begin 3 2 if over over < begin nop end drop drop end", None),
        ("fn foo begin if true true begin nop end end", ConditionTypeError),
        ("fn foo begin true if dup begin nop end drop end", None),
        ("fn foo begin 3 if drop 2 true begin nop end drop end", None),
        ('fn foo begin 3 if drop "" true begin nop end drop end', ConditionTypeError),
        ("fn foo begin while 3 begin nop end end", ConditionTypeError),
        ("fn foo begin while 3 true begin nop end end", ConditionTypeError),
        ("fn foo begin while true begin nop end end", None),
        ("fn foo begin while true true begin nop end end", ConditionTypeError),
        ("fn foo begin while 3 2 < begin nop end end", None),
        ("fn foo begin 3 2 while < begin nop end end", ConditionTypeError),
        ("fn foo begin 3 2 while over over < begin nop end drop drop end", None),
        ("fn foo begin while true begin 3 end end", LoopTypeError),
        ("fn foo begin while true begin 3 drop end end", None),
        ("fn foo args a as int begin a a - . end", None),
        ("fn foo args a as int begin a a + . end", None),
        ("fn foo args *a begin nop end", None),
        ("fn foo args *a return *a, *a begin a a end", None),
        ("fn foo args *a return *b begin a end", UnknownPlaceholderType),
        ("fn five return int begin 5 end fn foo return int begin five end", None),
        ("fn foo return int begin foo end", None),
        ("fn foo begin nop end fn foo begin nop end", FunctionNameCollision),
        ("fn foo begin bar end", UnknownFunction),
        ("fn foo args a as int, a as int begin nop end", ArgumentNameCollision),
        ("fn foo args foo as int begin nop end", ArgumentNameCollision),
        ("fn foo args a as bool begin nop end", None),
        ("fn foo args int as bool begin nop end", ParseError),
        ("fn int args begin nop end", ParseError),
    ],
)
def test_type_checker(
    code: str,
    expected_exception: Optional[Type[Exception]],
) -> None:
    code = f"fn main begin nop end\n{code}"
    program = Program.without_file(code)

    if expected_exception:
        assert len(program.file_load_errors) == 1
        assert type(program.file_load_errors[0]) == expected_exception
    else:
        assert not program.file_load_errors

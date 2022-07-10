from typing import Optional, Type

import pytest

from lang.runtime.program import Program
from lang.typing.exceptions import (
    ArgumentNameCollision,
    BranchTypeError,
    ConditionTypeError,
    FunctionNameCollision,
    FunctionTypeError,
    GetFieldOfNonStructTypeError,
    InvalidMemberFunctionSignature,
    LoopTypeError,
    SetFieldOfNonStructTypeError,
    StackTypesError,
    StackUnderflowError,
    StructUpdateStackError,
    StructUpdateTypeError,
    UnknownFunction,
    UnknownPlaceholderType,
    UnknownStructField,
)


@pytest.mark.parametrize(
    ["code", "expected_exception"],
    [
        ("fn foo { nop }", None),
        ("fn foo { drop }", StackUnderflowError),
        ("fn foo { 3 }", FunctionTypeError),
        ("fn foo { 3 drop }", None),
        ('fn foo { "a" "b" - }', StackTypesError),
        ('fn foo { "a" 3 - }', StackTypesError),
        ("fn foo return int { 5 }", None),
        ("fn foo return bool { 5 }", FunctionTypeError),
        ('fn foo return int, str { 5 "foo" }', None),
        ('fn foo return str, int { 5 "foo" }', FunctionTypeError),
        ("fn foo return int, int { 5 dup }", None),
        ("fn foo return bool, int, bool { true 5 over }", None),
        ("fn foo { 5 5 = drop }", None),
        ('fn foo { "" "" = drop }', None),
        ("fn foo { if true { nop } }", None),
        ("fn foo { if 3 { nop } }", ConditionTypeError),
        ("fn foo { if 3 true { nop } }", ConditionTypeError),
        ("fn foo { if true { nop else nop } }", None),
        ("fn foo { if true { 3 else nop } }", BranchTypeError),
        ("fn foo { if true { nop else 3 } }", BranchTypeError),
        ("fn foo { if true { 3 } }", BranchTypeError),
        ("fn foo { if 3 2 < { nop } }", None),
        ("fn foo { 3 2 if < { nop } }", ConditionTypeError),
        ("fn foo { 3 2 if over over < { nop } drop drop }", None),
        ("fn foo { if true true { nop } }", ConditionTypeError),
        ("fn foo { true if dup { nop } drop }", None),
        ("fn foo { 3 if drop 2 true { nop } drop }", None),
        ('fn foo { 3 if drop "" true { nop } drop }', ConditionTypeError),
        ("fn foo { while 3 { nop } }", ConditionTypeError),
        ("fn foo { while 3 true { nop } }", ConditionTypeError),
        ("fn foo { while true { nop } }", None),
        ("fn foo { while true true { nop } }", ConditionTypeError),
        ("fn foo { while 3 2 < { nop } }", None),
        ("fn foo { 3 2 while < { nop } }", ConditionTypeError),
        ("fn foo { 3 2 while over over < { nop } drop drop }", None),
        ("fn foo { while true { 3 } }", LoopTypeError),
        ("fn foo { while true { 3 drop } }", None),
        ("fn foo args a as int { a a - . }", None),
        ("fn foo args a as int { a a + . }", None),
        ("fn foo args a as *a { nop }", None),
        ("fn foo args a as *a return *a, *a { a a }", None),
        ("fn foo args a as *a return *b { a }", UnknownPlaceholderType),
        ("fn five return int { 5 } fn foo return int { five }", None),
        ("fn foo return int { foo }", None),
        ("fn foo { nop } fn foo { nop }", FunctionNameCollision),
        ("fn foo { bar }", UnknownFunction),
        ("fn foo args a as int, a as int { nop }", ArgumentNameCollision),
        ("fn foo args foo as int { nop }", ArgumentNameCollision),
        ("fn foo args a as bool { nop }", None),
        ('fn foo { vec[int] "" vec:push . }', StackTypesError),
        ("fn foo { vec[int] 5 vec:push . }", None),
        ("fn foo args a as *a { a a - drop }", StackTypesError),
        ('fn foo { 3 "a" ? }', GetFieldOfNonStructTypeError),
        (
            'struct bar { x as int } fn foo { bar "y" ? . drop }',
            UnknownStructField,
        ),
        ('struct bar { x as int } fn foo { bar "x" ? . drop }', None),
        (
            'struct bar { x as int } fn foo { bar "y" { 3 } ! drop }',
            UnknownStructField,
        ),
        (
            'struct bar { x as int } fn foo { bar "x" { 3 } ! drop }',
            None,
        ),
        (
            'struct bar { x as int } fn foo { 5 "x" { 3 } ! drop }',
            SetFieldOfNonStructTypeError,
        ),
        (
            'struct bar { x as int } fn foo { bar "x" { 34 } ! "x" ? . "\\n" . drop }',
            None,
        ),
        (
            'struct bar { x as int } fn foo { bar "x" { 34 35 } ! "x" ? . "\\n" . drop }',
            StructUpdateStackError,
        ),
        (
            'struct bar { x as int } fn foo { bar "x" { 3 } ! drop }',
            None,
        ),
        (
            'struct bar { x as int } fn foo { bar "x" { false } ! drop }',
            StructUpdateTypeError,
        ),
        (
            "struct bar { x as int } fn bar:foo args b as bar return bar { bar }",
            None,
        ),
        (
            "struct bar { x as int } fn bar:foo { nop }",
            InvalidMemberFunctionSignature,
        ),
        (
            "struct bar { x as int } fn bar:foo args b as bar { nop }",
            InvalidMemberFunctionSignature,
        ),
        (
            "struct bar { x as int } fn bar:foo return bar { nop }",
            InvalidMemberFunctionSignature,
        ),
    ],
)
def test_type_checker(
    code: str,
    expected_exception: Optional[Type[Exception]],
) -> None:
    code = "fn main { nop }\n" + code
    program = Program.without_file(code)

    if expected_exception:
        assert len(program.file_load_errors) == 1
        assert type(program.file_load_errors[0]) == expected_exception
    else:
        assert not program.file_load_errors

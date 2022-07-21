from typing import Dict, List, Type

import pytest

from lang.exceptions.import_ import AbsoluteImportError, CyclicImportError
from lang.exceptions.misc import MainFunctionNotFound
from lang.exceptions.naming import (
    ArgumentNameCollision,
    CollidingIdentifier,
    UnknownArgumentType,
    UnknownIdentifier,
    UnknownPlaceholderType,
    UnknownStructField,
)
from lang.exceptions.runtime import AaaAssertionFailure
from lang.exceptions.typing import (
    BranchTypeError,
    ConditionTypeError,
    FunctionTypeError,
    GetFieldOfNonStructTypeError,
    InvalidMainSignuture,
    InvalidMemberFunctionSignature,
    LoopTypeError,
    SetFieldOfNonStructTypeError,
    StackTypesError,
    StackUnderflowError,
    StructUpdateStackError,
    StructUpdateTypeError,
)
from tests.aaa import check_aaa_full_source, check_aaa_full_source_multi_file


@pytest.mark.parametrize(
    ["code", "expected_exception_types"],
    [
        pytest.param(
            """
            fn foo args foo as int { nop }
            fn main { nop }
            """,
            [ArgumentNameCollision],
            id="funcname-argname-collision",
        ),
        pytest.param(
            """
            fn foo args bar as int, bar as int { nop }
            fn main { nop }
            """,
            [ArgumentNameCollision],
            id="argname-argname-collision",
        ),
        pytest.param(
            'fn main { if true { 3 } else { "" } }', [BranchTypeError], id="branch-type"
        ),
        pytest.param(
            "fn main { if 3 true { nop } }",
            [ConditionTypeError],
            id="condition-type-branch",
        ),
        pytest.param(
            "fn main { while 3 true { nop } }",
            [ConditionTypeError],
            id="condition-type-loop",
        ),
        pytest.param(
            """
            fn foo { nop }
            fn foo { nop }
            """,
            [CollidingIdentifier],
            id="funcname-funcname-collision",
        ),
        pytest.param("fn main { 5 }", [FunctionTypeError], id="function-type"),
        pytest.param("fn main { while true { 0 } }", [LoopTypeError], id="loop-type"),
        pytest.param('fn main { 3 " " + . }', [StackTypesError], id="stack-types"),
        pytest.param("fn main { drop }", [StackUnderflowError], id="stack-underflow"),
        pytest.param(
            """
            fn main { bar }
            """,
            [UnknownIdentifier],
            id="unknown-function",
        ),
        pytest.param(
            """
            fn foo return *a { nop }
            fn main { nop }
            """,
            [UnknownPlaceholderType],
            id="unknown-placeholder-type",
        ),
        pytest.param(
            """
            fn foo args bar as baz { nop }
            fn main { nop }
            """,
            [UnknownArgumentType],
            id="unknown-type",
            marks=pytest.mark.skip,
        ),
        pytest.param(
            """
            fn foo { 5 }
            fn bar { 5 "" + }
            fn main { nop }
            """,
            [FunctionTypeError, StackTypesError],
            id="multiple-errors",
        ),
        pytest.param(
            "fn main args a as int { nop }",
            [InvalidMainSignuture],
            id="invalid-main-signature",
        ),
        pytest.param(
            """
            from "/foo" import bar
            fn main { nop }
            """,
            [AbsoluteImportError],
            id="absolute-import",
        ),
        pytest.param(
            """
            fn foo { 3 "a" ? }
            fn main { nop }
            """,
            [GetFieldOfNonStructTypeError],
            id="get-field-of-non-struct",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "y" ? . drop }
            fn main { nop }
            """,
            [UnknownStructField],
            id="unknown-struct-field-get",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "y" { 3 } ! drop }
            fn main { nop }
            """,
            [UnknownStructField],
            id="unknown-struct-field-set",
        ),
        pytest.param(
            """
            fn foo { 5 "x" { 3 } ! drop }
            fn main { nop }
            """,
            [SetFieldOfNonStructTypeError],
            id="set-field-of-non-struct",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "x" { 34 35 } ! "x" ? . "\\n" . drop }
            fn main { nop }
            """,
            [StructUpdateStackError],
            id="struct-update-stack-error",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "x" { false } ! drop }
            fn main { nop }
            """,
            [StructUpdateTypeError],
            id="struct-update-type-error",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn bar:foo { nop }
            fn main { nop }
            """,
            [InvalidMemberFunctionSignature],
            id="member-func-without-arg-or-return-type",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn bar:foo args b as bar { nop }
            fn main { nop }
            """,
            [InvalidMemberFunctionSignature],
            id="member-func-without-return-type",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn bar:foo return bar { nop }
            fn main { nop }
            """,
            [InvalidMemberFunctionSignature],
            id="member-func-without-arg-type",
        ),
        pytest.param(
            """
            fn main { nop }
            struct main { x as int }
            """,
            [CollidingIdentifier],
            id="struct-name-collision",
        ),
        pytest.param(
            """
            fn foo { nop }
            """,
            [MainFunctionNotFound],
            id="main-not-found",
        ),
        pytest.param(
            """
            fn main { false assert }
            """,
            [AaaAssertionFailure],
            id="assertion-failure",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo args b as bar { nop }
            """,
            [UnknownArgumentType],
            id="unknown-argument-type",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo args m as main { nop }
            """,
            [UnknownArgumentType],
            id="function-name-as-argument-type",
        ),
    ],
)
def test_errors(code: str, expected_exception_types: List[Type[Exception]]) -> None:
    check_aaa_full_source(code, "", expected_exception_types)


@pytest.mark.parametrize(
    ["files", "expected_exception_types"],
    [
        pytest.param(
            {
                "main.aaa": """
                from "foo" import foo
                fn main { nop }
                """,
                "foo.aaa": """
                from "main" import main
                fn foo { nop }
                """,
            },
            [CyclicImportError],
            id="cyclic-import",
        ),
        pytest.param(
            {
                "main.aaa": """
                from "five" import five as foo
                from "five" import five as foo
                fn main { nop }
                """,
                "five.aaa": """
                fn five return int { 5 }
                """,
            },
            [CollidingIdentifier],
            id="import-naming-collision",
            marks=pytest.mark.skip,
        ),
    ],
)
def test_multi_file_errors(
    files: Dict[str, str], expected_exception_types: List[Type[Exception]]
) -> None:
    check_aaa_full_source_multi_file(files, "", expected_exception_types)

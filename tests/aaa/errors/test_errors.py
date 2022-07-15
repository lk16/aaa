from typing import List, Type

import pytest

from lang.typing.exceptions import (
    AbsoluteImportError,
    ArgumentNameCollision,
    BranchTypeError,
    ConditionTypeError,
    CyclicImportError,
    FunctionNameCollision,
    FunctionTypeError,
    InvalidMainSignuture,
    LoopTypeError,
    StackTypesError,
    StackUnderflowError,
    UnknownFunction,
    UnknownPlaceholderType,
    UnknownType,
)
from tests.aaa import check_aaa_full_source


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
            [FunctionNameCollision],
            id="funcname-funcname-collision",
        ),
        pytest.param("fn main { 5 }", [FunctionTypeError], id="function-type"),
        pytest.param("fn main { while true { 0 } }", [LoopTypeError], id="loop-type"),
        pytest.param('fn main { 3 " " + . }', [StackTypesError], id="stack-types"),
        pytest.param("fn main { drop }", [StackUnderflowError], id="stack-underflow"),
        pytest.param(
            """
            fn foo { bar }
            fn main { nop }
            """,
            [UnknownFunction],
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
            [UnknownType],
            id="unknown-type",
            marks=pytest.mark.skip,
        ),
        pytest.param(
            """
            fn foo { 5 } fn bar { 5 }
            fn main { nop }
            """,
            [FunctionTypeError, FunctionTypeError],
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
            "# TODO", [CyclicImportError], id="cyclic-import", marks=pytest.mark.skip
        ),
    ],
)
def test_errors(code: str, expected_exception_types: List[Type[Exception]]) -> None:
    check_aaa_full_source(code, "", expected_exception_types)

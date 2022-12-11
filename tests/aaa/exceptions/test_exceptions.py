from typing import Dict, Type

import pytest

from aaa.cross_referencer.exceptions import (
    CollidingIdentifier,
    ImportedItemNotFound,
    InvalidArgument,
    MainFunctionNotFound,
    MainIsNotAFunction,
    UnknownIdentifier,
)
from aaa.parser.exceptions import FileReadError
from aaa.simulator.exceptions import AaaAssertionFailure
from aaa.type_checker.exceptions import (
    BranchTypeError,
    ConditionTypeError,
    FunctionTypeError,
    InvalidMainSignuture,
    InvalidMemberFunctionSignature,
    LoopTypeError,
    StackTypesError,
    StructUpdateStackError,
    StructUpdateTypeError,
    UnknownField,
)
from tests.aaa import check_aaa_full_source, check_aaa_full_source_multi_file


@pytest.mark.parametrize(
    ["code", "expected_exception_type", "expected_exception_message"],
    [
        pytest.param(
            'fn main { if true { 3 } else { "" } }',
            BranchTypeError,
            "/foo/main.aaa:1:11 Function main has inconsistent stacks for branches\n"
            + "           before: \n"
            + "  after if-branch: int\n"
            + "after else-branch: str\n",
            id="branch-type",
        ),
        pytest.param(
            "fn main { if 3 true { nop } }",
            ConditionTypeError,
            "/foo/main.aaa:1:14 Function main has a condition type error\n"
            + "stack before: \n"
            + " stack after: int bool\n",
            id="condition-type-branch",
        ),
        pytest.param(
            "fn main { while 3 true { nop } }",
            ConditionTypeError,
            "/foo/main.aaa:1:17 Function main has a condition type error\n"
            + "stack before: \n"
            + " stack after: int bool\n",
            id="condition-type-loop",
        ),
        pytest.param(
            """
            fn foo { nop }
            fn foo { nop }
            fn main { nop }
            """,
            CollidingIdentifier,
            "/foo/main.aaa:3:13: function foo collides with:\n"
            + "/foo/main.aaa:2:13: function foo\n",
            id="funcname-funcname-collision",
        ),
        pytest.param(
            """
            fn bar { 5 }
            fn main { nop }
            """,
            FunctionTypeError,
            "/foo/main.aaa:2:13: Function bar returns wrong type(s)\n"
            + "expected return types: \n"
            + "   found return types: int\n",
            id="function-type",
        ),
        pytest.param(
            "fn main { while true { 0 } }",
            LoopTypeError,
            "/foo/main.aaa:1:11 Function main has a stack modification inside loop body\n"
            + "before loop: \n"
            + " after loop: int\n",
            id="loop-type",
        ),
        pytest.param(
            'fn main { 3 " " + . }',
            StackTypesError,
            "/foo/main.aaa:1:17 Function main has invalid stack types when calling +\n"
            + "Expected stack top: int int\n"
            + "       Found stack: int str\n",
            id="stack-types",
        ),
        pytest.param(
            "fn main { drop }",
            StackTypesError,
            "/foo/main.aaa:1:11 Function main has invalid stack types when calling drop\n"
            + "Expected stack top: A\n"
            + "       Found stack: \n",
            id="stack-types-underflow",
        ),
        pytest.param(
            """
            fn main { bar }
            """,
            UnknownIdentifier,
            "/foo/main.aaa:2:23: Usage of unknown identifier bar\n",
            id="unknown-function",
        ),
        pytest.param(
            """
            fn foo return A { nop }
            fn main { nop }
            """,
            UnknownIdentifier,
            "/foo/main.aaa:2:27: Usage of unknown identifier A\n",
            id="unknown-placeholder-type",
        ),
        pytest.param(
            "fn main args a as int { nop }",
            InvalidMainSignuture,
            "/foo/main.aaa:1:1 Main function should have no arguments and no return types\n",
            id="invalid-main-signature-argument",
        ),
        pytest.param(
            "fn main { 5 }",
            FunctionTypeError,
            "/foo/main.aaa:1:1: Function main returns wrong type(s)\n"
            + "expected return types: \n"
            + "   found return types: int\n",
            id="invalid-main-signature-return-type\n",
        ),
        pytest.param(
            "fn main args a as int { 5 }",
            InvalidMainSignuture,
            "/foo/main.aaa:1:1 Main function should have no arguments and no return types\n",
            id="invalid-main-signature-both",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "y" ? . drop }
            fn main { nop }
            """,
            UnknownField,
            "/foo/main.aaa:3:26: Usage of unknown field y of type bar",
            id="unknown-struct-field-get",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "y" { 3 } ! drop }
            fn main { nop }
            """,
            UnknownField,
            "/foo/main.aaa:3:26: Usage of unknown field y of type bar",
            id="unknown-struct-field-set",
        ),
        pytest.param(
            """
            fn foo { 5 "x" { 3 } ! drop }
            fn main { nop }
            """,
            UnknownField,
            "/foo/main.aaa:2:24: Usage of unknown field x of type int",
            id="set-field-of-non-struct",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "x" { 34 35 } ! "x" ? . "\\n" . drop }
            fn main { nop }
            """,
            StructUpdateStackError,
            "/foo/main.aaa:3:26 Function foo modifies stack incorrectly when updating struct field\n"
            + "  Expected: bar str <new field value> \n"
            + "    Found: bar str int int\n",
            id="struct-update-stack-error",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "x" { false } ! drop }
            fn main { nop }
            """,
            StructUpdateTypeError,
            "/foo/main.aaa:3:32 Function foo tries to update struct field with wrong type\n"
            + "Attempt to set field x of bar to wrong type in foo\n"
            + "Expected type: str"
            + "\n   Found type: bool\n"
            + "\n"
            + "Type stack: bar str bool\n",
            id="struct-update-type-error",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn bar:foo { nop }
            fn main { nop }
            """,
            InvalidMemberFunctionSignature,
            "/foo/main.aaa:3:13 Function bar:foo has invalid member-function signature\n"
            + "\n"
            + "Expected arg types: bar ...\n"
            + "   Found arg types: \n",
            id="member-func-without-arg-or-return-type",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn bar:foo return bar { nop }
            fn main { nop }
            """,
            InvalidMemberFunctionSignature,
            "/foo/main.aaa:3:13 Function bar:foo has invalid member-function signature\n"
            + "\n"
            + "Expected arg types: bar ...\n"
            + "   Found arg types: \n",
            id="member-func-without-arg-type",
        ),
        pytest.param(
            """
            fn main { nop }
            fn bar { nop }
            struct bar { x as int }
            """,
            CollidingIdentifier,
            "/foo/main.aaa:3:13: function bar collides with:\n"
            + "/foo/main.aaa:4:13: type bar\n",
            id="struct-name-collision",
        ),
        pytest.param(
            """
            struct main { x as int }
            """,
            MainIsNotAFunction,
            "/foo/main.aaa: Found type main instead of function main",
            id="struct-name-collision",
        ),
        pytest.param(
            """
            fn foo { nop }
            """,
            MainFunctionNotFound,
            "/foo/main.aaa: No main function found",
            id="main-not-found",
        ),
        pytest.param(
            """
            fn main { false assert }
            """,
            AaaAssertionFailure,
            "/foo/main.aaa:2:29: Assertion failure, stacktrace:\n- main\n",
            id="assertion-failure",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo args b as bar { nop }
            """,
            UnknownIdentifier,
            "/foo/main.aaa:3:30: Usage of unknown identifier bar\n",
            id="unknown-argument-type",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo args m as main { nop }
            """,
            InvalidArgument,
            "/foo/main.aaa:3:30: Cannot use main as argument\n"
            + "/foo/main.aaa:2:13: function main collides\n",
            id="invalid-type-parameter",
        ),
    ],
)
def test_one_error(
    code: str, expected_exception_type: Type[Exception], expected_exception_message: str
) -> None:
    tmp_dir, exceptions = check_aaa_full_source(code, "", [expected_exception_type])

    assert len(exceptions) == 1
    exception_message = str(exceptions[0])

    exception_message = exception_message.replace(tmp_dir, "/foo")
    assert exception_message == expected_exception_message


@pytest.mark.parametrize(
    ["files", "expected_exception_type", "expected_exception_message"],
    [
        pytest.param(
            {
                "main.aaa": """
                from "five" import six as foo
                fn main { nop }
                """,
                "five.aaa": """
                fn five return int { 5 }
                """,
            },
            ImportedItemNotFound,
            "/foo/main.aaa:2:36: Could not import six from /foo/five.aaa\n",
            id="imported-item-not-found",
        ),
        pytest.param(
            {},
            FileReadError,
            "/foo/main.aaa: Failed to open or read\n",
            id="file-not-found",
        ),
    ],
)
def test_multi_file_errors(
    files: Dict[str, str],
    expected_exception_type: Type[Exception],
    expected_exception_message: str,
) -> None:
    tmp_dir, exceptions = check_aaa_full_source_multi_file(
        files, "", [expected_exception_type]
    )

    assert len(exceptions) == 1
    exception_message = str(exceptions[0])

    exception_message = exception_message.replace(tmp_dir, "/foo")
    assert exception_message == expected_exception_message


@pytest.mark.parametrize(
    ["files", "expected_exception_message"],
    [
        pytest.param(
            {
                "main.aaa": """
                fn bar { nop }
                fn foo args bar as int { nop }
                fn main { nop }
                """
            },
            "/foo/main.aaa:3:36: function argument bar collides with:\n"
            + "/foo/main.aaa:2:17: function bar\n",
            id="argname-other-func-name",
        ),
        pytest.param(
            {
                "main.aaa": """
                fn foo args foo as int { nop }
                fn main { nop }
                """
            },
            "/foo/main.aaa:2:36: function argument foo collides with:\n"
            + "/foo/main.aaa:2:17: function foo\n",
            id="argname-same-funcname",
        ),
        pytest.param(
            {
                "main.aaa": """
                fn foo args bar as int, bar as int { nop }
                fn main { nop }
                """
            },
            "/foo/main.aaa:2:29: function argument bar collides with:\n"
            + "/foo/main.aaa:2:41: function argument bar\n",
            id="argname-argname",
        ),
        pytest.param(
            {
                "main.aaa": """
                struct bar { x as int }
                fn foo args bar as int { nop }
                fn main { nop }
                """
            },
            "/foo/main.aaa:3:36: function argument bar collides with:\n"
            + "/foo/main.aaa:2:17: type bar\n",
            id="argname-struct",
        ),
        pytest.param(
            {
                "main.aaa": """
                from "five" import five
                fn foo args five as int { nop }
                fn main { nop }
                """,
                "five.aaa": """
               fn five return int { 5 }
                """,
            },
            "/foo/main.aaa:3:37: function argument five collides with:\n"
            + "/foo/main.aaa:2:36: function five\n",
            id="argname-import",
        ),
        pytest.param(
            {
                "main.aaa": """
                fn foo { nop }
                fn foo { nop }
                fn main { nop }
                """
            },
            "/foo/main.aaa:3:17: function foo collides with:\n"
            + "/foo/main.aaa:2:17: function foo\n",
            id="funcname-funcname",
        ),
        pytest.param(
            {
                "main.aaa": """
                struct foo { x as int }
                fn foo { nop }
                fn main { nop }
                """
            },
            "/foo/main.aaa:3:17: function foo collides with:\n"
            + "/foo/main.aaa:2:17: type foo\n",
            id="funcname-struct",
        ),
        pytest.param(
            {
                "main.aaa": """
                from "five" import five
                fn five { nop }
                fn main { nop }
                """,
                "five.aaa": """
               fn five return int { 5 }
                """,
            },
            "/foo/main.aaa:2:36: imported identifier five collides with:\n"
            + "/foo/main.aaa:3:17: function five\n",
            id="funcname-import",
        ),
        pytest.param(
            {
                "main.aaa": """
                fn foo { nop }
                struct foo { x as int }
                fn main { nop }
                """,
            },
            "/foo/main.aaa:2:17: function foo collides with:\n"
            + "/foo/main.aaa:3:17: type foo\n",
            id="struct-funcname",
        ),
        pytest.param(
            {
                "main.aaa": """
                struct foo { x as int }
                struct foo { x as int }
                fn main { nop }
                """,
            },
            "/foo/main.aaa:3:17: type foo collides with:\n"
            + "/foo/main.aaa:2:17: type foo\n",
            id="struct-struct",
        ),
        pytest.param(
            {
                "main.aaa": """
                from "five" import five
                struct five { x as int }
                fn main { nop }
                """,
                "five.aaa": """
               fn five return int { 5 }
                """,
            },
            "/foo/main.aaa:2:36: imported identifier five collides with:\n"
            + "/foo/main.aaa:3:17: type five\n",
            id="struct-import",
        ),
        pytest.param(
            {
                "main.aaa": """
                from "five" import five as bar
                fn foo args bar as int { nop }
                fn main { nop }
                """,
                "five.aaa": """
               fn five return int { 5 }
                """,
            },
            "/foo/main.aaa:3:36: function argument bar collides with:\n"
            + "/foo/main.aaa:2:36: function five\n",
            id="argname-import-renamed",
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
            "/foo/main.aaa:3:36: imported identifier foo collides with:\n"
            + "/foo/main.aaa:2:36: function five\n",
            id="import-import",
        ),
    ],
)
def test_colliding_identifier(
    files: Dict[str, str], expected_exception_message: str
) -> None:
    tmp_dir, exceptions = check_aaa_full_source_multi_file(
        files, "", [CollidingIdentifier]
    )

    assert len(exceptions) == 1
    exception_message = str(exceptions[0])
    exception_message = exception_message.replace(tmp_dir, "/foo")

    print(repr(exception_message))
    print()
    assert exception_message == expected_exception_message

from typing import Dict, Type

import pytest

from lang.exceptions.import_ import (
    AbsoluteImportError,
    CyclicImportError,
    FileReadError,
    ImportedItemNotFound,
)
from lang.exceptions.misc import MainFunctionNotFound
from lang.exceptions.naming import (
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
    StructUpdateStackError,
    StructUpdateTypeError,
)
from tests.aaa import check_aaa_full_source, check_aaa_full_source_multi_file


@pytest.mark.parametrize(
    ["code", "expected_exception_type", "expected_exception_message"],
    [
        pytest.param(
            'fn main { if true { 3 } else { "" } }',
            BranchTypeError,
            "/foo/main.aaa:1:1 Function main has inconsistent stacks for branches\n"
            + "           before: \n"
            + "  after if-branch: int\n"
            + "after else-branch: str\n",
            id="branch-type",
        ),
        pytest.param(
            "fn main { if 3 true { nop } }",
            ConditionTypeError,
            "/foo/main.aaa:1:1 Function main has a condition type error\n"
            + "stack before: \n"
            + " stack after: int bool\n",
            id="condition-type-branch",
        ),
        pytest.param(
            "fn main { while 3 true { nop } }",
            ConditionTypeError,
            "/foo/main.aaa:1:1 Function main has a condition type error\n"
            + "stack before: \n"
            + " stack after: int bool\n",
            id="condition-type-loop",
        ),
        pytest.param(  # TODO try other combinations
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
            "/foo/main.aaa:1:1 Function main has a stack modification inside loop body\n"
            + "before loop: \n"
            + " after loop: int\n",
            id="loop-type",
        ),
        pytest.param(
            'fn main { 3 " " + . }',
            StackTypesError,
            "/foo/main.aaa:1:1 Function main has invalid stack types when calling +\n"
            + "Expected stack top: str str\n"
            + "       Found stack: int str\n",
            id="stack-types",
        ),
        pytest.param(
            "fn main { drop }",
            StackTypesError,
            "/foo/main.aaa:1:1 Function main has invalid stack types when calling drop\n"
            + "Expected stack top: *a\n"
            + "       Found stack: \n",
            id="stack-types-underflow",
        ),
        pytest.param(
            """
            fn main { bar }
            """,
            UnknownIdentifier,
            "/foo/main.aaa:2:23: Function main uses unknown identifier bar\n",
            id="unknown-function",
        ),
        pytest.param(
            """
            fn foo return *a { nop }
            fn main { nop }
            """,
            UnknownPlaceholderType,
            "/foo/main.aaa:2:13: Function foo uses unknown placeholder a\n",
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
            InvalidMainSignuture,
            "",
            id="invalid-main-signature-return-type",
            marks=pytest.mark.skip,
        ),
        pytest.param(
            "fn main args a as int { 5 }",
            InvalidMainSignuture,
            "",
            id="invalid-main-signature-both",
            marks=pytest.mark.skip,
        ),
        pytest.param(
            """
            from "/foo" import bar
            fn main { nop }
            """,
            AbsoluteImportError,
            "/foo/main.aaa:2:13: Absolute imports are forbidden",
            id="absolute-import",
        ),
        pytest.param(
            """
            fn foo { 3 "a" ? }
            fn main { nop }
            """,
            GetFieldOfNonStructTypeError,
            "/foo/main.aaa:2:28 Function foo tries to get field of non-struct value\n"
            + "  Type stack: int str\n"
            + "Expected top: <struct type> str \n",
            id="get-field-of-non-struct",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "y" ? . drop }
            fn main { nop }
            """,
            UnknownStructField,
            "/foo/main.aaa:3:13: Function foo tries to use non-existing field y of struct bar\n",
            id="unknown-struct-field-get",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "y" { 3 } ! drop }
            fn main { nop }
            """,
            UnknownStructField,
            "/foo/main.aaa:3:13: Function foo tries to use non-existing field y of struct bar\n",
            id="unknown-struct-field-set",
        ),
        pytest.param(
            """
            fn foo { 5 "x" { 3 } ! drop }
            fn main { nop }
            """,
            SetFieldOfNonStructTypeError,
            "/foo/main.aaa:2:34 Function foo tries to set field of non-struct value\n"
            + "  Type stack: int str int\n"
            + "Expected top: <struct type> str <type of field to update>\n",
            id="set-field-of-non-struct",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "x" { 34 35 } ! "x" ? . "\\n" . drop }
            fn main { nop }
            """,
            StructUpdateStackError,
            "/foo/main.aaa:3:40 Function foo modifies stack incorrectly when updating struct field\n"
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
            "/foo/main.aaa:3:40 Function foo tries to update struct field with wrong type\n"
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
            + "   Found arg types: \n"
            + "Expected return types: bar ...\n"
            + "   Found return types: \n",
            id="member-func-without-arg-or-return-type",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn bar:foo args b as bar { nop }
            fn main { nop }
            """,
            InvalidMemberFunctionSignature,
            "/foo/main.aaa:3:13 Function bar:foo has invalid member-function signature\n"
            + "\n"
            + "Expected return types: bar ...\n"
            + "   Found return types: \n",
            id="member-func-without-return-type",
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
            struct main { x as int }
            """,
            CollidingIdentifier,
            "/foo/main.aaa:3:13: struct main collides with:\n"
            + "/foo/main.aaa:2:13: function main\n",
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
            "",
            id="assertion-failure",
            marks=pytest.mark.skip,
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo args b as bar { nop }
            """,
            UnknownArgumentType,
            "/foo/main.aaa:3:13: Function foo has argument with unknown type bar\n",
            id="unknown-argument-type",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo args m as main { nop }
            """,
            UnknownArgumentType,
            "/foo/main.aaa:3:13: Function foo has argument with unknown type main\n",
            id="function-name-as-argument-type",
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
                from "foo" import foo
                fn main { nop }
                """,
                "foo.aaa": """
                from "main" import main
                fn foo { nop }
                """,
            },
            CyclicImportError,
            "",
            id="cyclic-import",
            marks=pytest.mark.skip,
        ),
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
            "/foo/main.aaa:2:17: Could not import six from five\n",
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
            "/foo/main.aaa:3:29: function argument bar collides with:\n"
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
            "/foo/main.aaa:2:29: function argument foo collides with:\n"
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
            "/foo/main.aaa:2:41: function argument bar collides with:\n"
            + "/foo/main.aaa:2:29: function argument bar\n",
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
            "/foo/main.aaa:3:29: function argument bar collides with:\n"
            + "/foo/main.aaa:2:17: struct bar\n",
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
            "/foo/main.aaa:3:29: function argument five collides with:\n"
            + "/foo/main.aaa:2:16: function five\n",
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
            "/foo/main.aaa:2:17: struct foo collides with:\n"
            + "/foo/main.aaa:3:17: function foo\n",
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
            "/foo/main.aaa:3:17: function five collides with:\n"
            + "/foo/main.aaa:2:17: imported identifier five\n",
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
            "/foo/main.aaa:3:17: struct foo collides with:\n"
            + "/foo/main.aaa:2:17: function foo\n",
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
            "/foo/main.aaa:3:17: struct foo collides with:\n"
            + "/foo/main.aaa:2:17: struct foo\n",
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
            "/foo/main.aaa:3:17: struct five collides with:\n"
            + "/foo/main.aaa:2:17: imported identifier five\n",
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
            "/foo/main.aaa:3:29: function argument bar collides with:\n"
            + "/foo/main.aaa:2:16: function five\n",
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
            "/foo/main.aaa:3:17: imported identifier foo collides with:\n"
            + "/foo/main.aaa:2:17: function five\n",
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

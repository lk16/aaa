from typing import Dict, Type

import pytest

from aaa.cross_referencer.exceptions import (
    CircularDependencyError,
    CollidingEnumVariant,
    CollidingIdentifier,
    ImportedItemNotFound,
    IndirectImportException,
    InvalidArgument,
    InvalidEnumType,
    InvalidEnumVariant,
    InvalidReturnType,
    InvalidType,
    UnexpectedTypeParameterCount,
    UnknownIdentifier,
)
from aaa.parser.exceptions import EndOfFileException
from aaa.tokenizer.exceptions import FileReadError
from aaa.type_checker.exceptions import (
    AssignConstValueError,
    AssignmentTypeError,
    BranchTypeError,
    CaseAsArgumentCountError,
    CaseEnumTypeError,
    CaseStackTypeError,
    CollidingVariable,
    ConditionTypeError,
    DuplicateCase,
    ForeachLoopTypeError,
    FunctionTypeError,
    InvalidCallWithTypeParameters,
    InvalidIterable,
    InvalidIterator,
    InvalidMainSignuture,
    InvalidMemberFunctionSignature,
    InvalidTestSignuture,
    MainFunctionNotFound,
    MatchTypeError,
    MemberFunctionTypeNotFound,
    MissingEnumCases,
    MissingIterable,
    ReturnTypesError,
    StackTypesError,
    StructUpdateStackError,
    StructUpdateTypeError,
    UnknownField,
    UnknownVariableOrFunction,
    UnreachableCode,
    UnreachableDefaultBlock,
    UpdateConstStructError,
    UseBlockStackUnderflow,
    UseFieldOfEnumException,
    WhileLoopTypeError,
)
from tests.aaa import check_aaa_full_source, check_aaa_full_source_multi_file


@pytest.mark.parametrize(
    ["code", "expected_exception_type", "expected_exception_message"],
    [
        pytest.param(
            'fn main { if true { 3 } else { "" } }',
            BranchTypeError,
            "/foo/main.aaa:1:11: Inconsistent stacks for branches\n"
            + "           before: \n"
            + "  after if-branch: int\n"
            + "after else-branch: str\n",
            id="branch-type",
        ),
        pytest.param(
            "fn main { if 3 true { nop } }",
            ConditionTypeError,
            "/foo/main.aaa:1:14: Condition type error\n"
            + "stack before: \n"
            + " stack after: int bool\n",
            id="condition-type-branch",
        ),
        pytest.param(
            "fn main { while 3 true { nop } }",
            ConditionTypeError,
            "/foo/main.aaa:1:17: Condition type error\n"
            + "stack before: \n"
            + " stack after: int bool\n",
            id="condition-type-while-loop",
        ),
        pytest.param(
            """
            fn foo { nop }
            fn foo { nop }
            fn main { nop }
            """,
            CollidingIdentifier,
            "Found name collision:\n"
            + "/foo/main.aaa:2:13: function foo\n"
            + "/foo/main.aaa:3:13: function foo\n",
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
            WhileLoopTypeError,
            "/foo/main.aaa:1:11: Invalid stack modification inside while loop body\n"
            + "before while loop: \n"
            + " after while loop: int\n",
            id="while-loop-type",
        ),
        pytest.param(
            'fn main { 3 " " + . }',
            StackTypesError,
            "/foo/main.aaa:1:17: Invalid stack types when calling +\n"
            + "Expected stack top: (const int) (const int)\n"
            + "       Found stack: int str\n",
            id="stack-types",
        ),
        pytest.param(
            "fn main { drop }",
            StackTypesError,
            "/foo/main.aaa:1:11: Invalid stack types when calling drop\n"
            + "Expected stack top: A\n"
            + "       Found stack: \n",
            id="stack-types-underflow",
        ),
        pytest.param(
            """
            fn main { bar }
            """,
            UnknownVariableOrFunction,
            "/foo/main.aaa:2:23: Usage of unknown variable or function bar\n",
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
            "/foo/main.aaa:1:1: Main function has wrong signature, it should have:\n"
            + "- no type parameters\n"
            + "- either no arguments or one vec[str] argument\n"
            + "- return either nothing or an int\n",
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
            "fn main[A] { nop }",
            InvalidMainSignuture,
            "/foo/main.aaa:1:1: Main function has wrong signature, it should have:\n"
            + "- no type parameters\n"
            + "- either no arguments or one vec[str] argument\n"
            + "- return either nothing or an int\n",
            id="invalid-main-type-params",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "y" ? . drop }
            fn main { nop }
            """,
            UnknownField,
            "/foo/main.aaa:3:26: Usage of unknown field y of type bar\n",
            id="unknown-struct-field-get",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "y" { 3 } ! drop }
            fn main { nop }
            """,
            UnknownField,
            "/foo/main.aaa:3:26: Usage of unknown field y of type bar\n",
            id="unknown-struct-field-set",
        ),
        pytest.param(
            """
            fn foo { 5 "x" { 3 } ! drop }
            fn main { nop }
            """,
            UnknownField,
            "/foo/main.aaa:2:24: Usage of unknown field x of type int\n",
            id="set-field-of-non-struct",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "x" { 34 35 } ! "x" ? . "\\n" . drop }
            fn main { nop }
            """,
            StructUpdateStackError,
            "/foo/main.aaa:3:26: Incorrect stack modification when updating struct field\n"
            + "  Expected: bar str <new field value> \n"
            + "     Found: bar str int int\n",
            id="struct-update-stack-error",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn foo { bar "x" { false } ! drop }
            fn main { nop }
            """,
            StructUpdateTypeError,
            "/foo/main.aaa:3:32: Attempt to set field x of bar to wrong type\n"
            + "Expected type: int"
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
            "/foo/main.aaa:3:13: Function bar:foo has invalid member-function signature\n"
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
            "/foo/main.aaa:3:13: Function bar:foo has invalid member-function signature\n"
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
            "Found name collision:\n"
            + "/foo/main.aaa:3:13: function bar\n"
            + "/foo/main.aaa:4:13: struct bar\n",
            id="struct-name-collision",
        ),
        pytest.param(
            """
            struct main { x as int }
            """,
            MainFunctionNotFound,
            "/foo/main.aaa: No main function found\n",
            id="struct-named-main",
        ),
        pytest.param(
            """
            fn foo { nop }
            """,
            MainFunctionNotFound,
            "/foo/main.aaa: No main function found\n",
            id="main-not-found",
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
        pytest.param(
            """
            fn main { nop }
            fn bar[bar] { nop }
            """,
            CollidingIdentifier,
            "Found name collision:\n"
            + "/foo/main.aaa:3:13: function bar\n"
            + "/foo/main.aaa:3:20: struct bar\n",
            id="funcname-param-collision",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo[bar] args bar as int { nop }
            """,
            CollidingIdentifier,
            "Found name collision:\n"
            + "/foo/main.aaa:3:20: struct bar\n"
            + "/foo/main.aaa:3:30: function argument bar\n",
            id="argument-param-collision",
        ),
        pytest.param(
            "fn main { vec[int,int] drop }",
            UnexpectedTypeParameterCount,
            "/foo/main.aaa:1:11: Unexpected number of type parameters\n"
            + "Expected parameter count: 1\n"
            + "   Found parameter count: 2\n",
            id="call-with-too-many-type-params",
        ),
        pytest.param(
            "fn main { vec drop }",
            UnexpectedTypeParameterCount,
            "/foo/main.aaa:1:11: Unexpected number of type parameters\n"
            + "Expected parameter count: 1\n"
            + "   Found parameter count: 0\n",
            id="call-with-too-few-type-params",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo args a as vec[int,int] { nop }
            """,
            UnexpectedTypeParameterCount,
            "/foo/main.aaa:3:25: Unexpected number of type parameters\n"
            + "Expected parameter count: 1\n"
            + "   Found parameter count: 2\n",
            id="argument-with-too-many-type-params",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo args a as vec { nop }
            """,
            UnexpectedTypeParameterCount,
            "/foo/main.aaa:3:25: Unexpected number of type parameters\n"
            + "Expected parameter count: 1\n"
            + "   Found parameter count: 0\n",
            id="argument-with-too-few-type-params",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo return main { nop }
            """,
            InvalidReturnType,
            "/foo/main.aaa:2:13: Cannot use function main as return type\n",
            id="return-func-name",
        ),
        pytest.param(
            """
            fn main { nop }
            fn bar return vec[main] { nop }
            """,
            InvalidType,
            "/foo/main.aaa:2:13: Cannot use function main as type\n",
            id="function-as-return-type-param",
        ),
        pytest.param(
            """
            fn main { nop }
            fn bar return vec { nop }
            """,
            UnexpectedTypeParameterCount,
            "/foo/main.aaa:3:27: Unexpected number of type parameters\n"
            + "Expected parameter count: 1\n"
            + "   Found parameter count: 0\n",
            id="returntype-with-too-few-type-params",
        ),
        pytest.param(
            """
            fn main { nop }
            fn bar return vec[int,int] { nop }
            """,
            UnexpectedTypeParameterCount,
            "/foo/main.aaa:3:27: Unexpected number of type parameters\n"
            + "Expected parameter count: 1\n"
            + "   Found parameter count: 2\n",
            id="returntype-with-too-many-type-params",
        ),
        pytest.param(
            """
            fn main { foreach { nop } }
            """,
            MissingIterable,
            "/foo/main.aaa:2:23: Cannot use foreach, function stack is empty.\n",
            id="missing-iterable",
        ),
        pytest.param(
            """
            fn main { 0 foreach { nop } }
            """,
            InvalidIterable,
            "/foo/main.aaa:2:25: Invalid iterable type int.\n"
            + "Iterable types need to have a function named iter which:\n"
            + "- takes one argument (the iterable)\n"
            + "- returns one value (an iterator)\n",
            id="invalid-iterable-no-next-func",
        ),
        pytest.param(
            """
            struct foo { x as int }
            fn foo:iter args f as foo, y as int return int { 0 }
            fn main { foo foreach { nop } }
            """,
            InvalidIterable,
            "/foo/main.aaa:4:27: Invalid iterable type foo.\n"
            + "Iterable types need to have a function named iter which:\n"
            + "- takes one argument (the iterable)\n"
            + "- returns one value (an iterator)\n",
            id="invalid-iterable-iter-two-arguments",
        ),
        pytest.param(
            """
            struct foo { x as int }
            fn foo:iter args f as foo return int, int { 0 0 }
            fn main { foo foreach { nop } }
            """,
            InvalidIterable,
            "/foo/main.aaa:4:27: Invalid iterable type foo.\n"
            + "Iterable types need to have a function named iter which:\n"
            + "- takes one argument (the iterable)\n"
            + "- returns one value (an iterator)\n",
            id="invalid-iterable-iter-two-return-values",
        ),
        pytest.param(
            """
            struct foo { x as int }
            fn foo:iter args f as foo { nop }
            fn main { foo foreach { nop } }
            """,
            InvalidIterable,
            "/foo/main.aaa:4:27: Invalid iterable type foo.\n"
            + "Iterable types need to have a function named iter which:\n"
            + "- takes one argument (the iterable)\n"
            + "- returns one value (an iterator)\n",
            id="invalid-iterable-iter-no-return-values",
        ),
        pytest.param(
            """
            struct foo { x as int }
            fn foo:iter args f as foo return never { 0 exit }
            fn main { foo foreach { nop } }
            """,
            InvalidIterable,
            "/foo/main.aaa:4:27: Invalid iterable type foo.\n"
            + "Iterable types need to have a function named iter which:\n"
            + "- takes one argument (the iterable)\n"
            + "- returns one value (an iterator)\n",
            id="invalid-iterable-iter-no-return-values",
        ),
        pytest.param(
            """
            struct bar { x as int }
            struct foo { x as int }
            fn foo:iter args f as foo return bar { bar }
            fn main { foo foreach { nop } }
            """,
            InvalidIterator,
            "/foo/main.aaa:5:27: Invalid iterator type bar to iterate over foo.\n"
            + "Iterator types need to have a function named next which:\n"
            + "- takes one argument (the iterator)\n"
            + "- returns at least 2 values, the last being a boolean\n"
            + "- indicates if more data is present in the iterable with this last return value\n"
            + "- for const iterators all return values of `next` except the last one must be const\n",
            id="invalid-iterator-no-iter-func",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn bar:next args b as bar, y as int return int, bool { 0 false }
            struct foo { x as int }
            fn foo:iter args f as foo return bar { bar }
            fn main { foo foreach { nop } }
            """,
            InvalidIterator,
            "/foo/main.aaa:6:27: Invalid iterator type bar to iterate over foo.\n"
            + "Iterator types need to have a function named next which:\n"
            + "- takes one argument (the iterator)\n"
            + "- returns at least 2 values, the last being a boolean\n"
            + "- indicates if more data is present in the iterable with this last return value\n"
            + "- for const iterators all return values of `next` except the last one must be const\n",
            id="invalid-iterator-two-arguments",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn bar:next args b as bar, y as int return bool { false }
            struct foo { x as int }
            fn foo:iter args f as foo return bar { bar }
            fn main { foo foreach { nop } }
            """,
            InvalidIterator,
            "/foo/main.aaa:6:27: Invalid iterator type bar to iterate over foo.\n"
            + "Iterator types need to have a function named next which:\n"
            + "- takes one argument (the iterator)\n"
            + "- returns at least 2 values, the last being a boolean\n"
            + "- indicates if more data is present in the iterable with this last return value\n"
            + "- for const iterators all return values of `next` except the last one must be const\n",
            id="invalid-iterator-one-return-value",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn bar:next args b as bar, y as int return int, int { 0 0 }
            struct foo { x as int }
            fn foo:iter args f as foo return bar { bar }
            fn main { foo foreach { nop } }
            """,
            InvalidIterator,
            "/foo/main.aaa:6:27: Invalid iterator type bar to iterate over foo.\n"
            + "Iterator types need to have a function named next which:\n"
            + "- takes one argument (the iterator)\n"
            + "- returns at least 2 values, the last being a boolean\n"
            + "- indicates if more data is present in the iterable with this last return value\n"
            + "- for const iterators all return values of `next` except the last one must be const\n",
            id="invalid-iterator-no-last-bool-return-value",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn bar:next args b as bar, y as int return never { 0 exit }
            struct foo { x as int }
            fn foo:iter args f as foo return bar { bar }
            fn main { foo foreach { nop } }
            """,
            InvalidIterator,
            "/foo/main.aaa:6:27: Invalid iterator type bar to iterate over foo.\n"
            + "Iterator types need to have a function named next which:\n"
            + "- takes one argument (the iterator)\n"
            + "- returns at least 2 values, the last being a boolean\n"
            + "- indicates if more data is present in the iterable with this last return value\n"
            + "- for const iterators all return values of `next` except the last one must be const\n",
            id="invalid-iterator-never-return",
        ),
        pytest.param(
            """
            fn main { vec[int] foreach { nop } }
            """,
            ForeachLoopTypeError,
            "/foo/main.aaa:2:32: Invalid stack modification inside foreach loop body\n"
            + f"before foreach loop: vec[int]\n"
            + f" after foreach loop: vec[int] int\n",
            id="foreach-loop-type-error",
        ),
        pytest.param(
            """
            fn main { use a { nop } }
            """,
            UseBlockStackUnderflow,
            "/foo/main.aaa:2:23: Use block consumes more values than can be found on the stack\n"
            + "    stack size: 0\n"
            + "used variables: 1\n",
            id="use-block-stack-underflow",
        ),
        pytest.param(
            """
            fn main { 0 use a { a <- { false } } }
            """,
            AssignmentTypeError,
            "/foo/main.aaa:2:33: Assignment with wrong number and/or type of values\n"
            + "expected types: int\n"
            + "   found types: bool\n",
            id="assignment-type-error-wrong-type",
        ),
        pytest.param(
            """
            fn main { 0 use a { a <- { nop } } }
            """,
            AssignmentTypeError,
            "/foo/main.aaa:2:33: Assignment with wrong number and/or type of values\n"
            + "expected types: int\n"
            + "   found types: \n",
            id="assignment-type-error-empty-stack",
        ),
        pytest.param(
            """
            fn main { 0 use a { a <- { "" false } } }
            """,
            AssignmentTypeError,
            "/foo/main.aaa:2:33: Assignment with wrong number and/or type of values\n"
            + "expected types: int\n"
            + "   found types: str bool\n",
            id="assignment-type-error-too-many-types",
        ),
        pytest.param(
            """
            fn main { 0 use a { a <- { 0 0 } } }
            """,
            AssignmentTypeError,
            "/foo/main.aaa:2:33: Assignment with wrong number and/or type of values\n"
            + "expected types: int\n"
            + "   found types: int int\n",
            id="assignment-type-error-one-too-much",
        ),
        pytest.param(
            """
            fn main { a <- { nop } }
            """,
            UnknownVariableOrFunction,
            "/foo/main.aaa:2:23: Usage of unknown variable or function a\n",
            id="unknown-var",
        ),
        pytest.param(
            """
            fn main { 0 0 use a { use a { nop } } }
            """,
            CollidingVariable,
            "Found name collision:\n"
            + "/foo/main.aaa:2:31: local variable a\n"
            + "/foo/main.aaa:2:39: local variable a\n",
            id="colliding-identifier-var-var",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo args a as int { 0 use a { nop } }
            """,
            CollidingVariable,
            "Found name collision:\n"
            + "/foo/main.aaa:3:25: function argument a\n"
            + "/foo/main.aaa:3:42: local variable a\n",
            id="colliding-identifier-var-arg",
        ),
        pytest.param(
            """
            struct bar { x as int }
            fn main { 0 use bar { nop } }
            """,
            CollidingVariable,
            "Found name collision:\n"
            + "/foo/main.aaa:2:13: struct bar\n"
            + "/foo/main.aaa:3:29: local variable bar\n",
            id="colliding-identifier-var-identifier",
        ),
        pytest.param(
            """
            fn main { 3 foo }
            fn foo args x as const int { x bar }
            fn bar args x as int { nop }
            """,
            StackTypesError,
            "/foo/main.aaa:3:44: Invalid stack types when calling bar\n"
            + "Expected stack top: int\n"
            + "       Found stack: (const int)\n",
            id="stack-types-error-const",
        ),
        pytest.param(
            """
            struct foo { x as int }
            fn foo:bar args f as const foo { f "x" { 3 } ! }
            fn main { nop }
            """,
            UpdateConstStructError,
            "/foo/main.aaa:3:48: Cannot update field x on const struct foo\n",
            id="update-const-struct",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo args x as const int { x <- { 3 } }
            """,
            AssignConstValueError,
            "/foo/main.aaa:3:42: Cannot assign to (const int) x\n",
            id="assign-to-const-value",
        ),
        pytest.param(
            """
            struct foo { x as int }
            fn foo:bar args f as const foo { f "x" ? use x { x <- { 3 } } }
            fn main { nop }
            """,
            AssignConstValueError,
            "/foo/main.aaa:3:62: Cannot assign to (const int) x\n",
            id="assign-to-const-value",
        ),
        pytest.param(
            """
            fn main { 3 make_const use x { x <- { 5 } } }
            """,
            AssignConstValueError,
            "/foo/main.aaa:2:44: Cannot assign to (const int) x\n",
            id="assign-to-const-value-makeconst",
        ),
        pytest.param(
            "fn",
            EndOfFileException,
            "/foo/main.aaa: Parsing failed, unexpected end of file.\n",
            id="end-of-file-exception",
        ),
        pytest.param(
            "fn main { 3 use c { c[int] } }",
            InvalidCallWithTypeParameters,
            "/foo/main.aaa:1:21: Cannot use variable c with type parameters\n",
            id="invalid-call-with-type-params-argument",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo args a as int { a[b] drop }
            """,
            InvalidCallWithTypeParameters,
            "/foo/main.aaa:3:36: Cannot use argument a with type parameters\n",
            id="invalid-call-with-type-params-argument",
        ),
        pytest.param(
            'fn main return str { "" }',
            InvalidMainSignuture,
            "/foo/main.aaa:1:1: Main function has wrong signature, it should have:\n"
            + "- no type parameters\n"
            + "- either no arguments or one vec[str] argument\n"
            + "- return either nothing or an int\n",
            id="main-returning-wrong-type",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo return never { 0 }
            """,
            FunctionTypeError,
            "/foo/main.aaa:3:13: Function foo returns wrong type(s)\n"
            + "expected return types: never\n"
            + "   found return types: int\n",
            id="return-with-return-type-never",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo return int { false }
            """,
            FunctionTypeError,
            "/foo/main.aaa:3:13: Function foo returns wrong type(s)\n"
            + "expected return types: int\n"
            + "   found return types: bool\n",
            id="return-wrong-type",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo return int { false return }
            """,
            ReturnTypesError,
            "/foo/main.aaa:3:39: Invalid stack types when returning.\n"
            + "function returns: int\n"
            + "     found stack: bool\n",
            id="return-wrong-type-explicit",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo return vec[int] { vec[bool] }
            """,
            FunctionTypeError,
            "/foo/main.aaa:3:13: Function foo returns wrong type(s)\n"
            + "expected return types: vec[int]\n"
            + "   found return types: vec[bool]\n",
            id="return-wrong-type-param",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo return const int { 5 }
            """,
            FunctionTypeError,
            "/foo/main.aaa:3:13: Function foo returns wrong type(s)\n"
            + "expected return types: (const int)\n"
            + "   found return types: int\n",
            id="return-not-const",
        ),
        pytest.param(
            """
            fn main { nop }
            fn foo return int { 5 return 3 }
            """,
            UnreachableCode,
            "/foo/main.aaa:3:42: Found unreachable code.\n",
            id="unreachable-code",
        ),
        pytest.param(
            """
            enum foo { a as int }
            fn main { match { case main:bar { nop } } }
            """,
            InvalidEnumType,
            "/foo/main.aaa:3:31: Cannot use function main as enum type\n",
            id="invalid-enum-type-non-enum",
        ),
        pytest.param(
            """
            fn main { match { case int:bar { nop } } }
            """,
            InvalidEnumType,
            "/foo/main.aaa:2:31: Cannot use struct int as enum type\n",
            id="use-non-type-as-enum-type",
        ),
        pytest.param(
            """
            enum foo { a as int }
            fn main { match { case foo:b { nop } } }
            """,
            InvalidEnumVariant,
            "/foo/main.aaa:3:31: Variant b of enum foo does not exist\n",
            id="non-existent-enum-variant",
        ),
        pytest.param(
            """
            enum foo { bar as int }
            fn main { match { case foo:bar { nop } } }
            """,
            MatchTypeError,
            "/foo/main.aaa:3:23: Cannot match on this stack:\n"
            + "expected stack types: <enum type>\n"
            + "   found stack types: \n",
            id="match-empty-stack",
        ),
        pytest.param(
            """
            enum foo { bar as int }
            fn main { 3 match { case foo:bar { nop } } }
            """,
            MatchTypeError,
            "/foo/main.aaa:3:25: Cannot match on this stack:\n"
            + "expected stack types: <enum type>\n"
            + "   found stack types: int\n",
            id="match-non-emum",
        ),
        pytest.param(
            """
            enum foo { bar as int }
            enum baz { quux as int }
            fn main { 3 foo:bar match { case baz:quux { nop } } }
            """,
            CaseEnumTypeError,
            "/foo/main.aaa:4:41: Cannot use case for enum baz when matching on enum foo\n",
            id="case-from-different-enum",
        ),
        pytest.param(
            """
            enum foo { a as int, b as int }
            fn main {
                3 foo:a
                match {
                    case foo:a { nop }
                    case foo:b { 5 }
                }
            }
            """,
            CaseStackTypeError,
            "Inconsistent stack types for match cases:\n"
            + "/foo/main.aaa:6:21: (case foo:a) int\n"
            + "/foo/main.aaa:7:21: (case foo:b) int int\n",
            id="case-stack-type-error",
        ),
        pytest.param(
            """
            enum foo { a as int, b as int }
            fn main { 3 foo:a match { case foo:a { nop } } }
            """,
            MissingEnumCases,
            "/foo/main.aaa:3:31: Missing cases for enum foo.\n- foo:b\n",
            id="missing-enum-case",
        ),
        pytest.param(
            """
            enum foo { a as int, b as int }
            fn main { 3 foo:a match { case foo:a { nop } case foo:a { nop } } }
            """,
            DuplicateCase,
            "Duplicate case found in match block:\n"
            + "/foo/main.aaa:3:39: case foo:a\n"
            + "/foo/main.aaa:3:58: case foo:a\n",
            id="duplicate-case",
        ),
        pytest.param(
            """
            enum foo { a as int, b as int }
            fn main { 3 foo:a match { default { nop } default { nop } } }
            """,
            DuplicateCase,
            "Duplicate case found in match block:\n"
            + "/foo/main.aaa:3:39: default\n"
            + "/foo/main.aaa:3:55: default\n",
            id="duplicate-default",
        ),
        pytest.param(
            """
            enum foo { a as int, b as int }
            fn main { 3 foo:a match { case foo:a { drop } case foo:b { drop } default { nop } } }
            """,
            UnreachableDefaultBlock,
            "/foo/main.aaa:3:79: Unreachable default block.\n",
            id="unreachable-default-block",
        ),
        pytest.param(
            """
            enum foo { x as int, x as int }
            fn main { nop }
            """,
            CollidingEnumVariant,
            "Duplicate enum variant name collision:\n"
            + "/foo/main.aaa:2:24: enum variant foo:x\n"
            + "/foo/main.aaa:2:34: enum variant foo:x\n",
            id="colliding-enum-variant",
        ),
        pytest.param(
            """
            enum foo { bar }
            fn main { foo match { case foo:bar as a, b, c { nop } } }
            """,
            CaseAsArgumentCountError,
            "/foo/main.aaa:3:35: Unexpected number of case-arguments.\n"
            + "Expected arguments: 3\n"
            + "   Found arguments: 0\n",
            id="case-as-argument-count-error",
        ),
        pytest.param(
            """
            enum Foo { bar as int }
            fn main {
                Foo
                match {
                    case Foo:bar as value {
                        3
                        use value {
                            nop
                        }
                    }
                }
            }
            """,
            CollidingVariable,
            "Found name collision:\n"
            + "/foo/main.aaa:6:37: local variable value\n"
            + "/foo/main.aaa:8:29: local variable value\n",
            id="case-as-use-collision",
        ),
        pytest.param(
            """
            enum Foo { bar as int }
            fn main {
                3
                use value {
                    Foo
                    match {
                        case Foo:bar as value {
                            nop
                        }
                    }
                }
            }
            """,
            CollidingVariable,
            "Found name collision:\n"
            + "/foo/main.aaa:5:21: local variable value\n"
            + "/foo/main.aaa:8:41: local variable value\n",
            id="use-case-as-collision",
        ),
        pytest.param(
            """
            enum Foo { bar as int }
            fn main { Foo "field" { 3 } ! }
            """,
            UseFieldOfEnumException,
            "/foo/main.aaa:3:27: Cannot set field on Enum\n",
            id="set-field-on-enum",
        ),
        pytest.param(
            """
            enum Foo { bar as int }
            fn main { Foo "field" ? drop }
            """,
            UseFieldOfEnumException,
            "/foo/main.aaa:3:27: Cannot get field on Enum\n",
            id="set-field-on-enum",
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
        pytest.param(
            {
                "main.aaa": """
                from "five" import five
                fn main { nop }
                """,
                "five.aaa": """
                from "six" import six
                fn five return int { six 1 - }
                """,
                "six.aaa": """
                from "five" import five
                fn six return int { five 1 + }
                """,
            },
            CircularDependencyError,
            "Circular dependency detected:\n"
            + "- /foo/main.aaa\n"
            + "- /foo/five.aaa\n"
            + "- /foo/six.aaa\n"
            + "- /foo/five.aaa\n",
            id="circular-dependency",
        ),
        pytest.param(
            {
                "main.aaa": """
            from \"foo\" import bar
            fn main { nop }
            """,
                "foo.aaa": 'from "bar" import bar',
                "bar.aaa": "fn bar { nop }",
            },
            IndirectImportException,
            "/foo/main.aaa:2:31: Indirect imports are forbidden.\n",
            id="indirect-import",
        ),
        pytest.param(
            {
                "main.aaa": """
                from "type" import foo
                fn foo:bar args f as foo { nop }
                fn main { foo foo:bar }
                """,
                "type.aaa": "struct foo { x as int }",
            },
            MemberFunctionTypeNotFound,
            "/foo/main.aaa:3:17: Cannot find type foo in same file as member function definition.\n",
            id="member-function-in-different-file",
        ),
        pytest.param(
            {
                "main.aaa": """
                from "test_foo" import test_bar
                fn main { nop }
                """,
                "test_foo.aaa": "fn test_bar args a as int { nop }",
            },
            InvalidTestSignuture,
            "/foo/test_foo.aaa:1:1: Test function test_bar should have no arguments and no return types\n",
            id="invalid-test-signature-args",
        ),
        pytest.param(
            {
                "main.aaa": """
                from "test_foo" import test_bar
                fn main { nop }
                """,
                "test_foo.aaa": "fn test_bar return int { 4 }",
            },
            InvalidTestSignuture,
            "/foo/test_foo.aaa:1:1: Test function test_bar should have no arguments and no return types\n",
            id="invalid-test-signature-return-types",
        ),
        pytest.param(
            {
                "main.aaa": """
                from "test_foo" import test_bar
                fn main { nop }
                """,
                "test_foo.aaa": "fn test_bar return never { 0 exit }",
            },
            InvalidTestSignuture,
            "/foo/test_foo.aaa:1:1: Test function test_bar should have no arguments and no return types\n",
            id="invalid-test-signature-return-never",
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
            "Found name collision:\n"
            + "/foo/main.aaa:2:17: function bar\n"
            + "/foo/main.aaa:3:29: function argument bar\n",
            id="argname-other-func-name",
        ),
        pytest.param(
            {
                "main.aaa": """
                fn foo args foo as int { nop }
                fn main { nop }
                """
            },
            "Found name collision:\n"
            + "/foo/main.aaa:2:17: function foo\n"
            + "/foo/main.aaa:2:29: function argument foo\n",
            id="argname-same-funcname",
        ),
        pytest.param(
            {
                "main.aaa": """
                fn foo args bar as int, bar as int { nop }
                fn main { nop }
                """
            },
            "Found name collision:\n"
            + "/foo/main.aaa:2:29: function argument bar\n"
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
            "Found name collision:\n"
            + "/foo/main.aaa:2:17: struct bar\n"
            + "/foo/main.aaa:3:29: function argument bar\n",
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
            "Found name collision:\n"
            + "/foo/main.aaa:2:36: imported identifier five\n"
            + "/foo/main.aaa:3:29: function argument five\n",
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
            "Found name collision:\n"
            + "/foo/main.aaa:2:17: function foo\n"
            + "/foo/main.aaa:3:17: function foo\n",
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
            "Found name collision:\n"
            + "/foo/main.aaa:2:17: struct foo\n"
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
            "Found name collision:\n"
            + "/foo/main.aaa:2:36: imported identifier five\n"
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
            "Found name collision:\n"
            + "/foo/main.aaa:2:17: function foo\n"
            + "/foo/main.aaa:3:17: struct foo\n",
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
            "Found name collision:\n"
            + "/foo/main.aaa:2:17: struct foo\n"
            + "/foo/main.aaa:3:17: struct foo\n",
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
            "Found name collision:\n"
            + "/foo/main.aaa:2:36: imported identifier five\n"
            + "/foo/main.aaa:3:17: struct five\n",
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
            "Found name collision:\n"
            + "/foo/main.aaa:2:36: imported identifier bar\n"
            + "/foo/main.aaa:3:29: function argument bar\n",
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
            "Found name collision:\n"
            + "/foo/main.aaa:2:36: imported identifier foo\n"
            + "/foo/main.aaa:3:36: imported identifier foo\n",
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

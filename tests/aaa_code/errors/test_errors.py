from pathlib import Path
from typing import List, Type

import pytest

from lang.runtime.program import FileLoadException, Program
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
from tests.aaa_code import check_aaa_full_source


@pytest.mark.parametrize(
    ["code", "expected_exception_types"],
    [
        pytest.param(
            "fn foo args foo as int { nop }\n"
            + "fn main { nop }",
            [ArgumentNameCollision]
        ),
        # ("argument_function_collision.aaa", [ArgumentNameCollision]),
        # ("branch_type.aaa", [BranchTypeError]),
        # ("condition_type_branch.aaa", [ConditionTypeError]),
        # ("condition_type_loop.aaa", [ConditionTypeError]),
        # ("function_function_collision.aaa", [FunctionNameCollision]),
        # ("function_type.aaa", [FunctionTypeError]),
        # ("loop_type.aaa", [LoopTypeError]),
        # ("stack_type.aaa", [StackTypesError]),
        # ("stack_underflow.aaa", [StackUnderflowError]),
        # ("unknown_function.aaa", [UnknownFunction]),
        # ("unknown_placeholder.aaa", [UnknownPlaceholderType]),
        # pytest.param("unknown_type.aaa", [UnknownType], marks=pytest.mark.skip),
        # ("multiple_errors.aaa", [FunctionTypeError, FunctionTypeError]),
        # ("invalid_main_signature.aaa", [InvalidMainSignuture]),
        # ("absolute_import.aaa", [AbsoluteImportError]),
        # ("cyclic_imports/main.aaa", [CyclicImportError]),
    ],
)
def test_exceptions(
    code: str, expected_exception_types: List[Type[FileLoadException]]
) -> None:
    check_aaa_full_source(code, "", expected_exception_types)

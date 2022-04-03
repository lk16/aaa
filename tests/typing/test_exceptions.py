from parser.parser.exceptions import ParseError
from parser.tokenizer.exceptions import TokenizerError
from pathlib import Path
from typing import List, Type

import pytest

from lang.runtime.program import FileLoadException, Program
from lang.typing.exceptions import (
    AbsoluteImportError,
    ArgumentNameCollision,
    BranchTypeError,
    ConditionTypeError,
    FunctionNameCollision,
    FunctionTypeError,
    ImportedItemNotFound,
    InvalidMainSignuture,
    LoopTypeError,
    StackTypesError,
    StackUnderflowError,
    UnknownFunction,
    UnknownPlaceholderType,
    UnknownType,
)


@pytest.mark.parametrize(
    ["filename", "exception_types"],
    [
        ("argument_argument_collision.aaa", [ArgumentNameCollision]),
        ("argument_function_collision.aaa", [ArgumentNameCollision]),
        ("branch_type.aaa", [BranchTypeError]),
        ("condition_type_branch.aaa", [ConditionTypeError]),
        ("condition_type_loop.aaa", [ConditionTypeError]),
        ("function_function_collision.aaa", [FunctionNameCollision]),
        ("function_type.aaa", [FunctionTypeError]),
        ("loop_type.aaa", [LoopTypeError]),
        ("stack_type.aaa", [StackTypesError]),
        ("stack_underflow.aaa", [StackUnderflowError]),
        ("unknown_function.aaa", [UnknownFunction]),
        ("unknown_placeholder.aaa", [UnknownPlaceholderType]),
        ("unknown_type.aaa", [UnknownType]),
        ("multiple_errors.aaa", [FunctionTypeError, FunctionTypeError]),
        ("tokenize_error.aaa", [TokenizerError]),
        ("parse_error.aaa", [ParseError]),
        ("invalid_main_signature.aaa", [InvalidMainSignuture]),
        ("absolute_import.aaa", [AbsoluteImportError]),
        ("imported_item_not_found.aaa", [ImportedItemNotFound]),
    ],
)
def test_exceptions(
    filename: str, exception_types: List[Type[FileLoadException]]
) -> None:
    file = Path(f"examples/errors/{filename}")

    program = Program(file)
    assert list(map(type, program.file_load_errors)) == exception_types

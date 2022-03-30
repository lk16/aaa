from pathlib import Path
from typing import Type

import pytest

from lang.program import Program
from lang.typing.exceptions import (
    ArgumentNameCollision,
    BranchTypeError,
    ConditionTypeError,
    FunctionNameCollision,
    FunctionTypeError,
    LoopTypeError,
    StackTypesError,
    StackUnderflowError,
    TypeException,
    UnknownFunction,
    UnknownPlaceholderType,
    UnknownType,
)


@pytest.mark.parametrize(
    ["filename", "type_exception"],
    [
        ("argument_argument_collision.aaa", ArgumentNameCollision),
        ("argument_function_collision.aaa", ArgumentNameCollision),
        ("branch_type.aaa", BranchTypeError),
        ("condition_type_branch.aaa", ConditionTypeError),
        ("condition_type_loop.aaa", ConditionTypeError),
        ("function_function_collision.aaa", FunctionNameCollision),
        ("function_type.aaa", FunctionTypeError),
        ("loop_type.aaa", LoopTypeError),
        ("stack_type.aaa", StackTypesError),
        ("stack_underflow.aaa", StackUnderflowError),
        ("unknown_function.aaa", UnknownFunction),
        ("unknown_placeholder.aaa", UnknownPlaceholderType),
        ("unknown_type.aaa", UnknownType),
    ],
)
def test_exceptions(filename: str, type_exception: Type[TypeException]) -> None:
    file = Path(f"examples/errors/{filename}")

    with pytest.raises(type_exception):
        Program(file, exit_on_error=False)

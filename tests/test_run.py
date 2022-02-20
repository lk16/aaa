from dataclasses import dataclass
from typing import List, Type

import pytest

from lang.exceptions import (
    StackNotEmptyAtExit,
    StackUnderflow,
    UnexpectedType,
    UnhandledOperationError,
)
from lang.run import run
from lang.types import (
    And,
    BoolPush,
    Divide,
    Drop,
    Dup,
    Equals,
    IntGreaterEquals,
    IntGreaterThan,
    IntLessEquals,
    IntLessThan,
    IntNotEqual,
    IntPush,
    Minus,
    Multiply,
    Not,
    Operation,
    Or,
    Over,
    Plus,
    Print,
    Rot,
    Swap,
)


@dataclass
class UnhandledOperation(Operation):
    ...


@pytest.mark.parametrize(
    ["operations", "expected_exception"],
    [
        ([UnhandledOperation()], UnhandledOperationError),
        ([IntPush(3)], StackNotEmptyAtExit),
    ],
)
def test_run_program_fails(
    operations: List[Operation], expected_exception: Type[Exception]
) -> None:
    with pytest.raises(expected_exception):
        run(operations)


def test_run_program_unexpected_type() -> None:
    operations: List[Operation] = [BoolPush(True), IntPush(3), Plus()]

    with pytest.raises(UnexpectedType):
        run(operations)


@pytest.mark.parametrize(
    ["operations"],
    [
        ([Print()],),
        ([Plus()],),
        ([IntPush(1), Plus()],),
        ([Minus()],),
        ([IntPush(1), Minus()],),
        ([Multiply()],),
        ([IntPush(1), Multiply()],),
        ([Divide()],),
        ([IntPush(1), Divide()],),
        ([And()],),
        ([BoolPush(True), And()],),
        ([Or()],),
        ([BoolPush(True), Or()],),
        ([Not()],),
        ([Equals()],),
        ([IntPush(1), Equals()],),
        ([IntLessThan()],),
        ([IntPush(1), IntLessThan()],),
        ([IntLessEquals()],),
        ([IntPush(1), IntLessEquals()],),
        ([IntGreaterThan()],),
        ([IntPush(1), IntGreaterThan()],),
        ([IntGreaterEquals()],),
        ([IntPush(1), IntGreaterEquals()],),
        ([IntNotEqual()],),
        ([IntPush(1), IntNotEqual()],),
        ([Drop()],),
        ([Dup()],),
        ([Swap()],),
        ([IntPush(1), Swap()],),
        ([Over()],),
        ([IntPush(1), Over()],),
        ([Rot()],),
        ([IntPush(1), Rot()],),
        ([IntPush(1), IntPush(1), Rot()],),
    ],
)
def test_run_program_stack_underflow(operations: List[Operation]) -> None:
    with pytest.raises(StackUnderflow):
        run(operations)

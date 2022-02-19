from typing import List, Type

import pytest
from pytest import CaptureFixture

from lang.exceptions import (
    InvalidJump,
    StackUnderflow,
    UnexpectedType,
    UnhandledOperationError,
)
from lang.operations import (
    And,
    BoolPrint,
    BoolPush,
    Divide,
    Drop,
    Dup,
    End,
    If,
    IntEquals,
    IntGreaterEquals,
    IntGreaterThan,
    IntLessEquals,
    IntLessThan,
    IntNotEqual,
    IntPrint,
    IntPush,
    Minus,
    Multiply,
    Not,
    Operation,
    Or,
    Over,
    Plus,
    Rot,
    Swap,
    UnhandledOperation,
)
from lang.run import run_program


@pytest.mark.parametrize(
    ["operations", "expected_output"],
    [
        ([], ""),
        ([IntPush(1)], ""),
        ([IntPush(1), IntPush(1)], ""),
        ([IntPush(1), IntPrint()], "1"),
        ([IntPush(1), IntPrint(), IntPush(2), IntPrint()], "12"),
        ([IntPush(6), IntPush(2), Plus(), IntPrint()], "8"),
        ([IntPush(6), IntPush(2), Minus(), IntPrint()], "4"),
        ([IntPush(6), IntPush(2), Multiply(), IntPrint()], "12"),
        ([IntPush(6), IntPush(2), Divide(), IntPrint()], "3"),
        ([BoolPush(True), If(4), IntPush(5), IntPrint(), End()], "5"),
        ([BoolPush(False), If(4), IntPush(5), IntPrint(), End()], ""),
    ],
)
def test_run_program_ok(
    operations: List[Operation], expected_output: str, capfd: CaptureFixture[str]
) -> None:
    run_program(operations)
    output, _ = capfd.readouterr()
    assert expected_output == output


@pytest.mark.parametrize(
    ["operations", "expected_exception"],
    [
        ([UnhandledOperation()], UnhandledOperationError),
        ([BoolPush(True), If(None)], InvalidJump),
    ],
)
def test_run_program_fails(
    operations: List[Operation], expected_exception: Type[Exception]
) -> None:
    with pytest.raises(expected_exception):
        run_program(operations)


def test_run_program_unexpected_type() -> None:
    operations: List[Operation] = [BoolPush(True), IntPrint()]

    with pytest.raises(UnexpectedType):
        run_program(operations)


@pytest.mark.parametrize(
    ["operations"],
    [
        ([IntPrint()],),
        ([Plus()],),
        ([IntPush(1), Plus()],),
        ([Minus()],),
        ([IntPush(1), Minus()],),
        ([Multiply()],),
        ([IntPush(1), Multiply()],),
        ([Divide()],),
        ([IntPush(1), Divide()],),
        ([BoolPrint()],),
        ([And()],),
        ([BoolPush(True), And()],),
        ([Or()],),
        ([BoolPush(True), Or()],),
        ([Not()],),
        ([IntEquals()],),
        ([IntPush(1), IntEquals()],),
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
        run_program(operations)

from typing import List

import pytest
from pytest import CaptureFixture

from lang.exceptions import StackUnderflow, UnhandledOperationError
from lang.operations import (
    Divide,
    IntPush,
    Minus,
    Multiply,
    Operation,
    Plus,
    PrintInt,
    UnhandledOperation,
)
from lang.run import run_program


@pytest.mark.parametrize(
    ["operations", "expected_output"],
    [
        ([], ""),
        ([IntPush(1)], ""),
        ([IntPush(1), IntPush(1)], ""),
        ([IntPush(1), PrintInt()], "1"),
        ([IntPush(1), PrintInt(), IntPush(2), PrintInt()], "12"),
        ([IntPush(6), IntPush(2), Plus(), PrintInt()], "8"),
        ([IntPush(6), IntPush(2), Minus(), PrintInt()], "4"),
        ([IntPush(6), IntPush(2), Multiply(), PrintInt()], "12"),
        ([IntPush(6), IntPush(2), Divide(), PrintInt()], "3"),
    ],
)
def test_run_program_ok(
    operations: List[Operation], expected_output: str, capfd: CaptureFixture[str]
) -> None:
    run_program(operations)
    output, _ = capfd.readouterr()
    assert expected_output == output


def test_run_program_fail() -> None:
    operations: List[Operation] = [UnhandledOperation()]

    with pytest.raises(UnhandledOperationError):
        run_program(operations)


@pytest.mark.parametrize(
    ["operations"],
    [
        ([PrintInt()],),
        ([Plus()],),
        ([IntPush(1), Plus()],),
        ([Minus()],),
        ([IntPush(1), Minus()],),
        ([Multiply()],),
        ([IntPush(1), Multiply()],),
        ([Divide()],),
        ([IntPush(1), Divide()],),
    ],
)
def test_run_program_stack_underflow(operations: List[Operation]) -> None:
    with pytest.raises(StackUnderflow):
        run_program(operations)

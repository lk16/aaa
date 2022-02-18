from typing import List

import pytest
from pytest import CaptureFixture

from lang.exceptions import StackUnderflow, UnhandledOperationError
from lang.operations import (
    Divide,
    Minus,
    Multiply,
    Operation,
    Plus,
    PrintInt,
    PushInt,
    UnhandledOperation,
)
from lang.run import run_program


@pytest.mark.parametrize(
    ["operations", "expected_output"],
    [
        ([], ""),
        ([PushInt(1)], ""),
        ([PushInt(1), PushInt(1)], ""),
        ([PushInt(1), PrintInt()], "1"),
        ([PushInt(1), PrintInt(), PushInt(2), PrintInt()], "12"),
        ([PushInt(6), PushInt(2), Plus(), PrintInt()], "8"),
        ([PushInt(6), PushInt(2), Minus(), PrintInt()], "4"),
        ([PushInt(6), PushInt(2), Multiply(), PrintInt()], "12"),
        ([PushInt(6), PushInt(2), Divide(), PrintInt()], "3"),
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
        ([PushInt(1), Plus()],),
        ([Minus()],),
        ([PushInt(1), Minus()],),
        ([Multiply()],),
        ([PushInt(1), Multiply()],),
        ([Divide()],),
        ([PushInt(1), Divide()],),
    ],
)
def test_run_program_stack_underflow(operations: List[Operation]) -> None:
    with pytest.raises(StackUnderflow):
        run_program(operations)

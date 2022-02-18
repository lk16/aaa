from typing import List

import pytest
from pytest import CaptureFixture

from lang.exceptions import StackUnderflow, UnhandledOperationError
from lang.operations import Operation, PrintInt, PushInt, UnhandledOperation
from lang.run import run_program


@pytest.mark.parametrize(
    ["operations", "expected_output"],
    [
        ([], ""),
        ([PushInt(1)], ""),
        ([PushInt(1), PushInt(1)], ""),
        ([PushInt(1), PrintInt()], "1"),
        ([PushInt(1), PrintInt(), PushInt(2), PrintInt()], "12"),
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
        ([UnhandledOperation()], UnhandledOperationError(UnhandledOperation())),
        ([PrintInt()], StackUnderflow()),
    ],
)
def test_run_program_fail(
    operations: List[Operation], expected_exception: Exception
) -> None:
    with pytest.raises(type(expected_exception)) as e:
        run_program(operations)

    expected_exception.args == e.value.args

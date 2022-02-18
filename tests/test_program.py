import pytest
from pytest import CaptureFixture

from lang.parse import parse
from lang.run import run_program


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        ("1", ""),
        ("1 int_print", "1"),
        ("1 2 + int_print", "3"),
        ("1 2 3 4 + + + int_print", "10"),
        ("1 2 3 * + int_print", "7"),
    ],
)
def test_run_program_ok(
    code: str, expected_output: str, capfd: CaptureFixture[str]
) -> None:
    operations = parse(code)
    run_program(operations)

    output, _ = capfd.readouterr()
    assert expected_output == output

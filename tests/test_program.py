import pytest
from pytest import CaptureFixture

from lang.parse import parse
from lang.run import run_program


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        ("1", ""),
        ("1 print_int", "1"),
        ("1 2 + print_int", "3"),
        ("1 2 3 4 + + + print_int", "10"),
        ("1 2 3 * + print_int", "7"),
    ],
)
def test_run_program_ok(
    code: str, expected_output: str, capfd: CaptureFixture[str]
) -> None:
    operations = parse(code)
    run_program(operations)

    output, _ = capfd.readouterr()
    assert expected_output == output

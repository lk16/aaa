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
        ("true bool_print", "true"),
        ("false bool_print", "false"),
        ("true false and bool_print", "false"),
        ("false not bool_print", "true"),
        ("false true or bool_print", "true"),
        ("2 3 = bool_print", "false"),
        ("3 3 = bool_print", "true"),
        ("2 3 > bool_print", "false"),
        ("2 3 < bool_print", "true"),
        ("2 3 <= bool_print", "true"),
        ("2 3 >= bool_print", "false"),
        ("2 3 != bool_print", "true"),
    ],
)
def test_run_program_ok(
    code: str, expected_output: str, capfd: CaptureFixture[str]
) -> None:
    operations = parse(code)
    run_program(operations)

    stdout, stderr = capfd.readouterr()
    assert expected_output == stdout
    assert "" == stderr

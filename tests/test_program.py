import pytest
from pytest import CaptureFixture

from lang.parse import parse
from lang.run import run_program


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        ("1", ""),
        ("1 .", "1"),
        ("1 2 + .", "3"),
        ("1 2 3 4 + + + .", "10"),
        ("1 2 3 * + .", "7"),
        ("true .", "true"),
        ("false .", "false"),
        ("true false and .", "false"),
        ("false not .", "true"),
        ("false true or .", "true"),
        ("2 3 = .", "false"),
        ("3 3 = .", "true"),
        ("2 3 > .", "false"),
        ("2 3 < .", "true"),
        ("2 3 <= .", "true"),
        ("2 3 >= .", "false"),
        ("2 3 != .", "true"),
        ("1 2 drop .", "1"),
        ("1 dup . .", "11"),
        ("1 2 swap . .", "12"),
        ("1 2 over . . .", "121"),
        ("1 2 3 rot . . .", "132"),
        ("true if 4 . end", "4"),
        ("false if 4 . end", ""),
        ("true if 4 . end 5 .", "45"),
        ("false if 4 . end 5 .", "5"),
        ("3 . true if 4 . end", "34"),
        ("3 . false if 4 . end", "3"),
        ("\\n", "\n"),
        ("true if 1 . else 0 . end", "1"),
        ("false if 1 . else 0 . end", "0"),
        ("7 . true if 1 . else 0 . end 8 .", "718"),
        ("7 . false if 1 . else 0 . end 8 .", "708"),
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

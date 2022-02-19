import pytest
from pytest import CaptureFixture

from lang.parse import parse
from lang.run import run_program
from lang.tokenize import tokenize


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        ("1 drop", ""),
        ("1 .", "1"),
        ("1 2 + .", "3"),
        ("1 2 3 4 + + + .", "10"),
        ("1 2 3 * + .", "7"),
        ("3 2 - . ", "1"),
        ("6 2 / . ", "3"),
        ("7 2 / . ", "3"),
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
        ("false while 1 . false end", ""),
        ("true while 1 . false end", "1"),
        ("false true true true while 1 . end", "111"),
        ("0 true while dup . 1 + dup 9 <= end drop", "0123456789"),
        ('"foo" .', "foo"),
        ('"\\\\" .', "\\"),
        ('"\\n" .', "\n"),
        ('"\\"" .', '"'),
        ('"a" "b" + .', "ab"),
        ('"aaa" "aaa" = .', "true"),
        ('"aaa" "bbb" = .', "false"),
        ('"abc" 0 2 substr .', "ab"),
        ('"abc" 0 5 substr .', "abc"),
        ('"abc" 1 2 substr .', "b"),
        ('"abc" 3 2 substr .', ""),
        ('"abc" 7 8 substr .', ""),
    ],
)
def test_run_program_ok(
    code: str, expected_output: str, capfd: CaptureFixture[str]
) -> None:
    tokens = tokenize(code, "<stdin>")
    operations = parse(tokens)
    run_program(operations)

    stdout, stderr = capfd.readouterr()
    assert expected_output == stdout
    assert "" == stderr

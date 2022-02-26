from dataclasses import dataclass
from typing import List, Type

import pytest
from pytest import CaptureFixture

from lang.exceptions import (
    StackNotEmptyAtExit,
    StackUnderflow,
    UnexpectedType,
    UnhandledOperationError,
)
from lang.operations import (
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
from lang.run import run_as_main


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
        run_as_main(operations)


def test_run_program_unexpected_type() -> None:
    operations: List[Operation] = [BoolPush(True), IntPush(3), Plus()]

    with pytest.raises(UnexpectedType):
        run_as_main(operations)


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
        run_as_main(operations)


@pytest.mark.skip
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
        ("// 1 .", ""),
        ("0 . \n// 1 .\n2 .", "02"),
        ("0 . \n1 . // 2 .\n3 .", "013"),
        ("0 . \n1 . // invalidcode\n3 .", "013"),
        ("7 3 % .", "1"),
        ('"" strlen .', "0"),
        ('"abc" strlen .', "3"),
    ],
)
def test_run_program_as_main_ok(
    code: str, expected_output: str, capfd: CaptureFixture[str]
) -> None:

    # TODO run code as main

    stdout, stderr = capfd.readouterr()
    assert expected_output == stdout
    assert "" == stderr

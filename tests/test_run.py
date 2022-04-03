from pathlib import Path
from typing import Dict, List, Optional, Type

import pytest
from pytest import CaptureFixture

from lang.runtime.program import FileLoadException, Program
from lang.runtime.simulator import Simulator


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
        ("if true begin 4 . end", "4"),
        ("if false begin 4 . end", ""),
        ("if true begin 4 . end 5 .", "45"),
        ("if false begin 4 . end 5 .", "5"),
        ("3 . if true begin 4 . end", "34"),
        ("3 . if false begin 4 . end", "3"),
        ("\\n", "\n"),
        ("if true begin 1 . else 0 . end", "1"),
        ("if false begin 1 . else 0 . end", "0"),
        ("7 . if true begin 1 . else 0 . end 8 .", "718"),
        ("7 . if false begin 1 . else 0 . end 8 .", "708"),
        ("while false begin 1 . end", ""),
        ("0 while dup 9 <= begin dup . 1 + end drop", "0123456789"),
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
        ("7 3 % .", "1"),
        ('"" strlen .', "0"),
        ('"abc" strlen .', "3"),
        ("if true begin nop end 3 .", "3"),
        ("if false begin nop end 3 .", "3"),
        ("if true begin 1 . end 3 .", "13"),
        ("if false begin 1 . end 3 .", "3"),
        ("if true begin nop else nop end 3 .", "3"),
        ("if false begin nop else nop end 3 .", "3"),
        ("if true begin 1 . else nop end 3 .", "13"),
        ("if false begin 1 . else nop end 3 .", "3"),
        ("if true begin nop else 2 . end 3 .", "3"),
        ("if false begin nop else 2 . end 3 .", "23"),
        ("if true begin 1 . else 2 . end 3 .", "13"),
        ("if false begin 1 . else 2 . end 3 .", "23"),
        ("while false begin nop end 3 .", "3"),
        ("nop", ""),
        ("nop // hi", ""),
        ("// hi\nnop", ""),
        ("//\nnop", ""),
        ("nop //\n", ""),
        ("if //\ntrue begin 3 . end", "3"),
        ("true assert", ""),
    ],
)
def test_program_run_ok(
    code: str, expected_output: str, capfd: CaptureFixture[str]
) -> None:

    code = f"fn main begin {code}\nend"
    program = Program.without_file(code)
    Simulator(program).run()

    stdout, stderr = capfd.readouterr()
    assert expected_output == stdout
    assert "" == stderr


def test_program_run_assertion_failure() -> None:
    code = "fn main begin false assert end"
    program = Program.without_file(code)
    with pytest.raises(SystemExit):
        Simulator(program).run()


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        ("fn main begin 1 print end fn print args a as int begin a . end", "1"),
        (
            "fn main begin 1 2 3 print end fn print args a as int, b as int, c as int begin a . b . c . end",
            "123",
        ),
        ("fn main begin foo end\n" + "fn foo begin 1 . end", "1"),
        (
            "fn main begin foo end\n"
            + "fn foo begin bar end\n"
            + "fn bar begin baz end\n"
            + "fn baz begin 1 . end",
            "1",
        ),
        (
            "fn main begin 1 2 3 foo end\n"
            + "fn foo args a as int, b as int, c as int begin a b c bar end\n"
            + "fn bar args a as int, b as int, c as int begin a b c baz end\n"
            + "fn baz args a as int, b as int, c as int begin a . b . c . end",
            "123",
        ),
        ("#!/usr/bin/env aaa\nfn main begin nop end", ""),
    ],
)
def test_prgram_full_source_ok(
    code: str, expected_output: str, capfd: CaptureFixture[str]
) -> None:
    program = Program.without_file(code)
    Simulator(program).run()

    stdout, stderr = capfd.readouterr()
    assert expected_output == stdout
    assert "" == stderr


@pytest.mark.parametrize(
    ["files", "expected_output", "expected_errors"],
    [
        (
            {
                "five.aaa": "fn five return int begin 5 end",
                "six.aaa": 'from "five" import five\n fn six return int begin five 1 + end',
                "main.aaa": 'from "six" import six\n fn main begin six . end',
            },
            "6",
            [],
        ),
        (
            {
                "add.aaa": "fn add args a as int, b as int, return int, begin a b + end",
                "main.aaa": 'from "add" import add,\n fn main begin 3 2 add . end',
            },
            "5",
            [],
        ),
    ],
)
def test_program_multi_file(
    files: Dict[str, str],
    expected_output: Optional[str],
    expected_errors: List[Type[FileLoadException]],
    tmp_path: Path,
    capfd: CaptureFixture[str],
) -> None:
    for filename, code in files.items():
        (tmp_path / filename).write_text(code)

    program = Program(tmp_path / "main.aaa")

    assert list(map(type, program.file_load_errors)) == expected_errors

    if not expected_errors:
        Simulator(program).run()
        stdout, stderr = capfd.readouterr()
        assert expected_output == stdout
        assert "" == stderr

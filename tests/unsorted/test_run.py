from pathlib import Path
from typing import Dict, List, Optional, Type

import pytest
from pytest import CaptureFixture

from lang.runtime.program import FileLoadException, Program
from lang.runtime.simulator import Simulator
from lang.typing.exceptions import MainFunctionNotFound


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        ("1 drop", ""),
        ("1 .", "1"),
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
        ("if true { 4 . }", "4"),
        ("if false { 4 . }", ""),
        ("if true { 4 . } 5 .", "45"),
        ("if false { 4 . } 5 .", "5"),
        ("3 . if true { 4 . }", "34"),
        ("3 . if false { 4 . }", "3"),
        ("if true { 1 . } else { 0 . }", "1"),
        ("if false { 1 . } else { 0 . }", "0"),
        ("7 . if true { 1 . } else { 0 . } 8 .", "718"),
        ("7 . if false { 1 . } else { 0 . } 8 .", "708"),
        ("while false { 1 . }", ""),
        ("0 while dup 9 <= { dup . 1 + } drop", "0123456789"),
        ('"foo" .', "foo"),
        ('"\\\\" .', "\\"),
        ('"\\n" .', "\n"),
        ('"\\"" .', '"'),
        ('"a" "b" + .', "ab"),
        ('"aaa" "aaa" = .', "true"),
        ('"aaa" "bbb" = .', "false"),
        ("if true { nop } 3 .", "3"),
        ("if false { nop } 3 .", "3"),
        ("if true { 1 . } 3 .", "13"),
        ("if false { 1 . } 3 .", "3"),
        ("if true { nop } else { nop } 3 .", "3"),
        ("if false { nop } else { nop } 3 .", "3"),
        ("if true { 1 . } else { nop } 3 .", "13"),
        ("if false { 1 . } else { nop } 3 .", "3"),
        ("if true { nop } else { 2 . } 3 .", "3"),
        ("if false { nop } else { 2 . } 3 .", "23"),
        ("if true { 1 . } else { 2 . } 3 .", "13"),
        ("if false { 1 . } else { 2 . } 3 .", "23"),
        ("while false { nop } 3 .", "3"),
        ("nop", ""),
        ("nop // hi", ""),
        ("// hi\nnop", ""),
        ("//\nnop", ""),
        ("nop //\n", ""),
        ("if //\ntrue { 3 . }", "3"),
        ("true assert", ""),
        ("int .", "0"),
        ("bool .", "false"),
        ("str .", ""),
        ("vec[int] .", "[]"),
        ("vec[vec[int]] .", "[]"),
        ("map[int, int] .", "{}"),
        ("map[int, map[int, int]] .", "{}"),
        ("vec[int] 5 vec:push .", "[5]"),
        ("vec[bool] true vec:push .", "[true]"),
        ('vec[str] "foo" vec:push .', '["foo"]'),
        ('vec[int] 5 vec:push vec:pop . " " . .', "5 []"),
        ('vec[int] 5 vec:push 0 vec:get . " " . .', "5 [5]"),
        ('vec[int] 5 vec:push 0 7 vec:set vec:pop . " " . .', "7 []"),
        ("vec[int] 5 vec:push vec:size . drop", "1"),
        ("vec[int] 5 vec:push vec:empty . drop", "false"),
        ("vec[int] vec:empty . drop", "true"),
        ("vec[int] 5 vec:push vec:clear vec:size . drop", "0"),
        (
            "vec[int] 5 vec:push vec:copy vec:clear vec:size . drop vec:size . drop",
            "01",
        ),
        (
            "vec[int] 5 vec:push dup vec:clear vec:size . drop vec:size . drop",
            "00",
        ),
        ("vec[vec[int]] vec[int] 5 vec:push vec:push .", "[[5]]"),
        ('map[str, int] "one" 1 map:set .', '{"one": 1}'),
        ('map[str, int] "one" 1 map:set "one" map:get . drop', "1"),
        ('map[str, int] "one" 1 map:set "one" 2 map:set "one" map:get . drop', "2"),
        ('map[str, int] "one" 1 map:set "one" map:has_key . drop', "true"),
        ('map[str, int] "one" 1 map:set "two" map:has_key . drop', "false"),
        ('map[str, int] "one" 1 map:set map:size . drop', "1"),
        ("map[str, int] map:size . drop", "0"),
        ('map[str, int] "one" 1 map:set map:empty . drop', "false"),
        ("map[str, int] map:empty . drop", "true"),
        ('map[str, int] "one" 1 map:set "one" map:pop drop map:size . drop', "0"),
        ('map[str, int] "one" 1 map:set map:clear map:size . drop', "0"),
        (
            'map[str, int] "one" 1 map:set map:copy map:clear map:size . drop map:size . drop',
            "01",
        ),
        (
            'map[str, int] "one" 1 map:set dup map:clear map:size . drop map:size . drop',
            "00",
        ),
    ],
)
def test_program_run_ok(
    code: str, expected_output: str, capfd: CaptureFixture[str]
) -> None:

    code = "fn main {\n" + code + "\n}"
    program = Program.without_file(code)
    assert not program.file_load_errors
    Simulator(program).run()

    stdout, stderr = capfd.readouterr()
    assert expected_output == stdout
    assert "" == stderr


def test_program_run_assertion_failure() -> None:
    code = "fn main { false assert }"
    program = Program.without_file(code)
    assert not program.file_load_errors
    with pytest.raises(SystemExit):
        Simulator(program).run()


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        ("fn main { 1 print } fn print args a as int { a . }", "1"),
        (
            "fn main { 1 2 3 print } fn print args a as int, b as int, c as int { a . b . c . }",
            "123",
        ),
        ("fn main { foo }\n" + "fn foo { 1 . }", "1"),
        (
            "fn main { foo }\n"
            + "fn foo { bar }\n"
            + "fn bar { baz }\n"
            + "fn baz { 1 . }",
            "1",
        ),
        (
            "fn main { 1 2 3 foo }\n"
            + "fn foo args a as int, b as int, c as int { a b c bar }\n"
            + "fn bar args a as int, b as int, c as int { a b c baz }\n"
            + "fn baz args a as int, b as int, c as int { a . b . c . }",
            "123",
        ),
        ("#!/usr/bin/env aaa\nfn main { nop }", ""),
        ('struct foo { x as int } fn main { foo "x" ? . drop }', "0"),
        ('struct foo { x as bool } fn main { foo "x" ? . drop }', "false"),
        ('struct foo { x as str } fn main { foo "x" ? . drop }', ""),
        ('struct foo { x as vec[int] } fn main { foo "x" ? . drop }', "[]"),
        (
            'struct foo { x as map[int, str] } fn main { foo "x" ? . drop }',
            "{}",
        ),
        (
            'struct foo { x as int } fn main { foo "x" { 3 } ! "x" ? . drop }',
            "3",
        ),
        (
            'struct foo { x as bool } fn main { foo "x" { true } ! "x" ? . drop }',
            "true",
        ),
        (
            'struct foo { x as str } fn main { foo "x" { "bar" } ! "x" ? . drop }',
            "bar",
        ),
        (
            'struct foo { x as vec[int] } fn main { foo "x" ? 5 vec:push drop "x" ? . drop }',
            "[5]",
        ),
        (
            'struct foo { x as map[int, str] } fn main { foo "x" ? 5 "five" map:set drop "x" ? . drop }',
            '{5: "five"}',
        ),
    ],
)
def test_program_full_source_ok(
    code: str, expected_output: str, capfd: CaptureFixture[str]
) -> None:
    program = Program.without_file(code)
    assert not program.file_load_errors
    Simulator(program).run()

    stdout, stderr = capfd.readouterr()
    assert expected_output == stdout
    assert "" == stderr


@pytest.mark.parametrize(
    ["files", "expected_output", "expected_errors"],
    [
        pytest.param(
            {
                "five.aaa": "fn five return int { 5 }",
                "six.aaa": 'from "five" import five\n fn six return int { five 1 + }',
                "main.aaa": 'from "six" import six\n fn main { six . }',
            },
            "6",
            [],
        ),
        pytest.param(
            {
                "add.aaa": "fn add args a as int, b as int, return int, { a b + }",
                "main.aaa": 'from "add" import add,\n fn main { 3 2 add . }',
            },
            "5",
            [],
        ),
        (
            {
                "main.aaa": "fn foo { nop }",
            },
            "",
            [MainFunctionNotFound],
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

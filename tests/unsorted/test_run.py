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

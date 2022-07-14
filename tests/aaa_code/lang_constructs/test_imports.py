from pathlib import Path
from typing import Dict, List, Optional, Type

import pytest
from pytest import CaptureFixture

from lang.runtime.program import FileLoadException, Program
from lang.runtime.simulator import Simulator
from lang.typing.exceptions import FileReadError, ImportedItemNotFound


@pytest.mark.parametrize(
    ["files", "expected_output", "expected_errors"],
    [
        pytest.param(
            {
                "add.aaa": "fn add args a as int, b as int, return int, { a b + }",
                "main.aaa": 'from "add" import add,\n fn main { 3 2 add . }',
            },
            "5",
            [],
            id="two-files",
        ),
        pytest.param(
            {
                "add.aaa": "fn add args a as int, b as int, return int, { a b + }",
                "main.aaa": 'from "add" import add as foo,\n fn main { 3 2 foo . }',
            },
            "5",
            [],
            id="two-files-alias",
        ),
        pytest.param(
            {
                "add.aaa": "fn add args a as int, b as int, return int, { a b + }",
                "main.aaa": 'from "add" import foo,\n fn main { 3 2 foo . }',
            },
            "5",
            [ImportedItemNotFound],
            id="two-files-nonexistent-function",
        ),
        pytest.param(
            {
                "main.aaa": 'from "add" import add,\n fn main { 3 2 add . }',
            },
            "5",
            [FileReadError],
            id="two-files-nonexistent-file",
        ),
        pytest.param(
            {
                "five.aaa": "fn five return int { 5 }",
                "six.aaa": 'from "five" import five\n fn six return int { five 1 + }',
                "main.aaa": 'from "six" import six\n fn main { six . }',
            },
            "6",
            [],
            id="three-files",
        ),
    ],
)
def test_imports(
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

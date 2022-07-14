from pathlib import Path
from typing import Dict, List, Optional, Type

import pytest
from pytest import CaptureFixture

from lang.runtime.program import FileLoadException, Program
from lang.runtime.simulator import Simulator
from lang.typing.exceptions import MainFunctionNotFound


@pytest.mark.parametrize(
    ["files", "expected_output", "expected_errors"],
    [
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

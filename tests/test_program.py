from pathlib import Path
from unittest.mock import patch

import pytest
from pytest import MonkeyPatch

from lang.runtime.program import Program
from lang.typing.exceptions import FileReadError, MissingEnvironmentVariable

pytestmark = pytest.mark.no_builtins_cache

BUILTINS_FILE_PATH = Path().cwd() / "stdlib/builtins.aaa"


def test_program_load_builtins_without_stdlib_path_env_var(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.delenv("AAA_STDLIB_PATH")

    program = Program.without_file("fn main { nop }")
    assert len(program.file_load_errors) == 1
    assert isinstance(program.file_load_errors[0], MissingEnvironmentVariable)


def test_pram_load_builtins_file_not_found() -> None:
    def my_read_text(path: Path) -> str:
        assert path == BUILTINS_FILE_PATH
        raise FileNotFoundError

    with patch.object(Path, "read_text", my_read_text):
        program = Program.without_file("fn main { nop }")

    assert len(program.file_load_errors) == 1
    assert isinstance(program.file_load_errors[0], FileReadError)
    assert program.file_load_errors[0].file == BUILTINS_FILE_PATH

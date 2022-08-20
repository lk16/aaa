import inspect
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from lang.models.instructions import Instruction
from lang.parser.exceptions import FileReadError
from lang.runtime.program import Program
from lang.runtime.simulator import Simulator

pytestmark = pytest.mark.no_builtins_cache

BUILTINS_FILE_PATH = Path().cwd() / "stdlib/builtins.aaa"


def test_program_load_builtins_file_not_found() -> None:
    def my_read_text(path: Path) -> str:
        assert path == BUILTINS_FILE_PATH
        raise FileNotFoundError

    with patch.object(Path, "read_text", my_read_text):
        program = Program.without_file("fn main { nop }")

    assert len(program.file_load_errors) == 1
    assert isinstance(program.file_load_errors[0], FileReadError)
    assert program.file_load_errors[0].file == BUILTINS_FILE_PATH


def test_program_load_builtins_ok() -> None:
    program = Program.without_file("fn main { nop }")
    assert len(program.file_load_errors) == 0


def test_program_implements_all_instructions() -> None:
    instruction_types = {
        obj
        for _, obj in inspect.getmembers(sys.modules["lang.models.instructions"])
        if inspect.isclass(obj)
        and issubclass(obj, Instruction)
        and obj is not Instruction
    }

    simulator = Simulator(Program.without_file("fn main { nop }"))
    implemented_instructions = set(simulator.instruction_funcs.keys())
    assert instruction_types == implemented_instructions

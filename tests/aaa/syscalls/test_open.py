from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import pytest

from lang.runtime.program import Program
from lang.runtime.simulator import Simulator

TEST_FD = 1337


@pytest.mark.skip()
def test_open_ok() -> None:
    def mock_open(path: str, flags: int, mode: int = 0o777) -> int:
        return TEST_FD

    program = Program.without_file('fn main { "foo.txt" 0 511 . . }')

    with patch("lang.runtime.simulator.os.open", mock_open):
        with redirect_stdout(StringIO()) as stdout:
            Simulator(program).run()

    assert stdout.getvalue() == f"true{TEST_FD}"


@pytest.mark.skip()
def test_open_fail() -> None:
    def mock_open(path: str, flags: int, mode: int = 0o777) -> int:
        raise FileNotFoundError

    program = Program.without_file('fn main { "foo.txt" 0 511 . drop }')

    with patch("lang.runtime.simulator.os.open", mock_open):
        with redirect_stdout(StringIO()) as stdout:
            Simulator(program).run()

    assert stdout.getvalue() == f"false"

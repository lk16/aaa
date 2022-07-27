from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from lang.runtime.program import Program
from lang.runtime.simulator import Simulator

TEST_FD = 1337


def test_close_ok() -> None:
    def mock_close(fd: int) -> None:
        pass

    program = Program.without_file("fn main { 2 close . }")
    simulator = Simulator(program)

    with patch("lang.runtime.simulator.os.close", mock_close):
        with redirect_stdout(StringIO()) as stdout:
            simulator.run()

    assert stdout.getvalue() == "true"


def test_close_fail() -> None:
    def mock_close(fd: int) -> None:
        raise OSError

    program = Program.without_file("fn main { 3 close . }")
    simulator = Simulator(program)

    with patch("lang.runtime.simulator.os.close", mock_close):
        with redirect_stdout(StringIO()) as stdout:
            simulator.run()

    assert stdout.getvalue() == "false"

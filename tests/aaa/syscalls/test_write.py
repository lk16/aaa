from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from lang.runtime.program import Program
from lang.runtime.simulator import Simulator

TEST_FD = 1337


def test_write_ok() -> None:
    def mock_write(fd: int, data: bytes) -> int:
        print(data.decode("utf-8"), end="")
        return len(data)

    program = Program.without_file('fn main { 1 "hello world\\n" write . . }')
    simulator = Simulator(program)

    with patch("lang.runtime.simulator.os.write", mock_write):
        with redirect_stdout(StringIO()) as stdout:
            simulator.run()

    assert stdout.getvalue() == "hello world\ntrue12"


def test_write_fail() -> None:
    def mock_write(fd: int, data: bytes) -> None:
        raise OSError

    program = Program.without_file('fn main { 4 "hello world\\n" write . . }')
    simulator = Simulator(program)

    with patch("lang.runtime.simulator.os.write", mock_write):
        with redirect_stdout(StringIO()) as stdout:
            simulator.run()

    assert stdout.getvalue() == "false0"

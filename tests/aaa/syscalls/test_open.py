from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from aaa.run import Runner

TEST_FD = 1337


def test_open_ok() -> None:
    def mock_open(path: str, flags: int, mode: int = 0o777) -> int:
        return TEST_FD

    runner = Runner.without_file('fn main { "foo.txt" 0 511 open . . }')

    with patch("lang.runtime.simulator.os.open", mock_open):
        with redirect_stdout(StringIO()) as stdout:
            runner.run()

    assert stdout.getvalue() == f"true{TEST_FD}"


def test_open_fail() -> None:
    def mock_open(path: str, flags: int, mode: int = 0o777) -> int:
        raise FileNotFoundError

    runner = Runner.without_file('fn main { "foo.txt" 0 511 open . drop }')

    with patch("lang.runtime.simulator.os.open", mock_open):
        with redirect_stdout(StringIO()) as stdout:
            runner.run()

    assert stdout.getvalue() == "false"

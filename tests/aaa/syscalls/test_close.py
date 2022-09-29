from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from aaa.run import Runner

TEST_FD = 1337


def test_close_ok() -> None:
    def mock_close(fd: int) -> None:
        pass

    runner = Runner.without_file("fn main { 2 close . }")

    with patch("aaa.simulator.simulator.os.close", mock_close):
        with redirect_stdout(StringIO()) as stdout:
            runner.run()

    assert stdout.getvalue() == "true"


def test_close_fail() -> None:
    def mock_close(fd: int) -> None:
        raise OSError

    runner = Runner.without_file("fn main { 3 close . }")

    with patch("aaa.simulator.simulator.os.close", mock_close):
        with redirect_stdout(StringIO()) as stdout:
            runner.run()

    assert stdout.getvalue() == "false"

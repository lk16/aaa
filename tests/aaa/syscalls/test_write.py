from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from aaa.run import Runner

TEST_FD = 1337


def test_write_ok() -> None:
    def mock_write(fd: int, data: bytes) -> int:
        print(data.decode("utf-8"), end="")
        return len(data)

    code = 'fn main { 1 "hello world\\n" write . . }'
    runner = Runner.without_file(code, None, False)

    with patch("aaa.simulator.simulator.os.write", mock_write):
        with redirect_stdout(StringIO()) as stdout:
            runner.run()

    assert stdout.getvalue() == "hello world\ntrue12"


def test_write_fail() -> None:
    def mock_write(fd: int, data: bytes) -> None:
        raise OSError

    code = 'fn main { 4 "hello world\\n" write . . }'
    runner = Runner.without_file(code, None, False)

    with patch("aaa.simulator.simulator.os.write", mock_write):
        with redirect_stdout(StringIO()) as stdout:
            runner.run()

    assert stdout.getvalue() == "false0"

from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from aaa.run import Runner

MOCK_SEC = 123456789
MOCK_NANO_SEC = 987654328  # NOTE: not ending in 1 because of float rounding errors


def test_gettimeofday() -> None:
    def mock_time() -> float:
        return MOCK_SEC + (MOCK_NANO_SEC / 1_000_000_000)

    code = 'fn main { gettimeofday . " " . . }'
    runner = Runner.without_file(code, None, False)

    with patch("aaa.simulator.simulator.time.time", mock_time):
        with redirect_stdout(StringIO()) as stdout:
            runner.run()

    assert stdout.getvalue() == f"{MOCK_NANO_SEC} {MOCK_SEC}"

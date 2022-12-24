from typing import Any
from unittest.mock import patch

from aaa.run import Runner


def test_unlink() -> None:
    def mock_unlink(*args: Any, **kwargs: Any) -> None:
        pass

    runner = Runner.without_file('fn main { "foo.txt" unlink . }', None, False)

    with patch("aaa.simulator.simulator.os.unlink", mock_unlink):
        runner.run()

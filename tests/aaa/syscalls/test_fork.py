from unittest.mock import patch

from tests.aaa import check_aaa_main

TEST_PID = 1337


def test_fork() -> None:
    def mock_fork() -> int:
        return TEST_PID

    with patch("lang.runtime.simulator.os.fork", mock_fork):
        check_aaa_main("fork .", f"{TEST_PID}", [])

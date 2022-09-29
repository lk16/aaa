from unittest.mock import patch

from tests.aaa import check_aaa_main

TEST_PID = 1337


def test_getpid() -> None:
    def mock_getpid() -> int:
        return TEST_PID

    with patch("lang.runtime.simulator.os.getpid", mock_getpid):
        check_aaa_main("getpid .", f"{TEST_PID}", [])

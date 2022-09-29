from unittest.mock import patch

from tests.aaa import check_aaa_main

TEST_PPID = 1337


def test_getppid() -> None:
    def mock_getppid() -> int:
        return TEST_PPID

    with patch("aaa.simulator.simulator.os.getppid", mock_getppid):
        check_aaa_main("getppid .", f"{TEST_PPID}", [])

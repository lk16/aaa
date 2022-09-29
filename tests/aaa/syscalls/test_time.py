from unittest.mock import patch

from tests.aaa import check_aaa_main

DUMMY_UNIX_TIMESTAMP = 123456789


def test_time() -> None:
    def mock_time() -> int:
        return DUMMY_UNIX_TIMESTAMP

    with patch("aaa.simulator.simulator.time.time", mock_time):
        check_aaa_main("time .", f"{DUMMY_UNIX_TIMESTAMP}", [])

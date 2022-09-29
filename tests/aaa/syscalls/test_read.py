from unittest.mock import patch

from tests.aaa import check_aaa_main

TEST_INPUT = "some test input"


def test_read_ok() -> None:
    def mock_read(fd: int, length: int) -> bytes:
        return bytes(TEST_INPUT, encoding="utf-8")

    with patch("aaa.simulator.simulator.os.read", mock_read):
        check_aaa_main('0 1024 read . " " . .', f"true {TEST_INPUT}", [])


def test_read_fail() -> None:
    def mock_read(fd: int, length: int) -> bytes:
        raise OSError

    with patch("aaa.simulator.simulator.os.read", mock_read):
        check_aaa_main('5 1024 read . " " . .', f"false ", [])

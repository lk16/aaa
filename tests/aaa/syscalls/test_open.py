from unittest.mock import patch

from tests.aaa import check_aaa_main

TEST_FD = 1337


def test_open_ok() -> None:
    def mock_open() -> int:
        return TEST_FD

    with patch("lang.runtime.simulator.os.open", mock_open):
        check_aaa_main('"foo.txt" 0 511 . .', f"true{TEST_FD}", [])


def test_open_fail() -> None:
    def mock_open() -> int:
        raise FileNotFoundError

    with patch("lang.runtime.simulator.os.open", mock_open):
        check_aaa_main('"foo.txt" 0 511 . drop', f"false", [])

from typing import Tuple
from unittest.mock import patch

from tests.aaa import check_aaa_main


def test_waitpid_ok() -> None:
    def mock_waitpid(pid: int, options: int) -> Tuple[int, int]:
        return 0, 3 << 8

    with patch("aaa.simulator.simulator.os.waitpid", mock_waitpid):
        check_aaa_main("1337 0 waitpid . .", f"true3", [])


def test_waitpid_fail() -> None:
    def mock_waitpid(pid: int, options: int) -> Tuple[int, int]:
        raise OSError

    with patch("aaa.simulator.simulator.os.waitpid", mock_waitpid):
        check_aaa_main("1337 0 waitpid . .", f"false0", [])

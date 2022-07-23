import os

from tests.aaa import check_aaa_main


def test_getcwd() -> None:
    code = "getcwd ."
    expected_output = os.getcwd()
    check_aaa_main(code, expected_output, [])

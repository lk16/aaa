import pytest

from tests.aaa import check_aaa_main


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        pytest.param("1 . while false { 2 . } 3 .", "13", id="false"),
        pytest.param(
            "1 . 2 while dup 4 <= { dup . 1 + } drop 5 .", "12345", id="true-false"
        ),
    ],
)
def test_loop(code: str, expected_output: str) -> None:
    check_aaa_main(code, expected_output, [])

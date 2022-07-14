import pytest

from tests.aaa_code import check_aaa_main


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        pytest.param("if true { 1 . }", "1", id="if-true"),
        pytest.param("if false { 1 . }", "", id="if-false"),
        pytest.param("1 . if true { 2 . } else { 3 . } 4 .", "124", id="if-else-true"),
        pytest.param(
            "1 . if false { 2 . } else { 3 . } 4 .", "134", id="if-else-false"
        ),
    ],
)
def test_if_else(code: str, expected_output: str) -> None:
    check_aaa_main(code, expected_output, [])

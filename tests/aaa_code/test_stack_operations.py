import pytest

from tests.aaa_code import check_aaa_main


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        pytest.param("1 drop", "", id="drop"),
        pytest.param("1 dup . .", "11", id="dup"),
        pytest.param("1 2 swap . .", "12", id="swap"),
        pytest.param("1 2 over . . .", "121", id="over"),
        pytest.param("1 2 3 rot . . .", "132", id="rot"),
    ],
)
def test_stack(code: str, expected_output: str) -> None:
    check_aaa_main(code, expected_output, [])

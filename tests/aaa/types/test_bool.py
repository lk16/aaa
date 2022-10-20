import pytest

from tests.aaa import check_aaa_main


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        pytest.param("true .", "true", id="print-true"),
        pytest.param("false .", "false", id="print-false"),
        pytest.param("bool .", "false", id="print-zero-value"),
    ],
)
def test_bool(code: str, expected_output: str) -> None:
    check_aaa_main(code, expected_output, [])

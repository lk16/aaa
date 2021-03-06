import pytest

from tests.aaa import check_aaa_main


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        pytest.param("true .", "true", id="print-true"),
        pytest.param("false .", "false", id="print-false"),
        pytest.param("bool .", "false", id="print-zero-value"),
        pytest.param("false not .", "true", id="not-false"),
        pytest.param("true not .", "false", id="not-true"),
        pytest.param("true true and .", "true", id="true-and-true"),
        pytest.param("true false and .", "false", id="true-and-false"),
        pytest.param("false true and .", "false", id="false-and-true"),
        pytest.param("false false and .", "false", id="false-and-false"),
        pytest.param("true true or .", "true", id="true-or-true"),
        pytest.param("true false or .", "true", id="true-or-false"),
        pytest.param("false true or .", "true", id="false-or-true"),
        pytest.param("false false or .", "false", id="false-or-false"),
    ],
)
def test_bool(code: str, expected_output: str) -> None:
    check_aaa_main(code, expected_output, [])

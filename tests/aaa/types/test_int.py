from typing import List, Type

import pytest

from tests.aaa import check_aaa_main


@pytest.mark.parametrize(
    ["code", "expected_output", "expected_exception_types"],
    [
        pytest.param("1 .", "1", [], id="print"),
        pytest.param("-1 .", "-1", [], id="print-negative"),
        pytest.param("int .", "0", [], id="print-zero-value"),
    ],
)
def test_int(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    check_aaa_main(code, expected_output, expected_exception_types)

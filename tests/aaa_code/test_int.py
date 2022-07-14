from typing import List, Type

import pytest

from tests.aaa_code import check_aaa_main


@pytest.mark.parametrize(
    ["code", "expected_output", "expected_exception_types"],
    [
        pytest.param("1 .", "1", [], id="print"),
        pytest.param("int .", "0", [], id="print-zero-value"),
        pytest.param("1 2 + .", "3", [], id="add-basic"),
        pytest.param("2 3 * .", "6", [], id="multiply-basic"),
        pytest.param("3 2 - .", "1", [], id="subtract-positive-result"),
        pytest.param("3 5 - .", "-2", [], id="subtract-negative-result"),
        pytest.param("6 3 / .", "2", [], id="devide-ok-evenly"),
        pytest.param("7 3 / .", "2", [], id="devide-ok-unevenly"),
        pytest.param("7 0 / .", "", [], id="devide-by-zero", marks=pytest.mark.skip),
        pytest.param("7 3 % .", "1", [], id="modulo-ok"),
        pytest.param("7 0 % .", "", [], id="modulo-zero", marks=pytest.mark.skip),
        pytest.param("2 3 = .", "false", [], id="2=3"),
        pytest.param("3 3 = .", "true", [], id="3=3"),
        pytest.param("3 2 > .", "true", [], id="3>2"),
        pytest.param("2 3 > .", "false", [], id="2>3"),
        pytest.param("2 2 > .", "false", [], id="2>2"),
        pytest.param("2 3 < .", "true", [], id="2<3"),
        pytest.param("3 2 < .", "false", [], id="3<2"),
        pytest.param("2 2 < .", "false", [], id="2<2"),
        pytest.param("2 3 <= .", "true", [], id="2<=3"),
        pytest.param("2 2 <= .", "true", [], id="2<=2"),
        pytest.param("3 2 <= .", "false", [], id="3<=2"),
        pytest.param("2 3 >= .", "false", [], id="2>=3"),
        pytest.param("2 2 >= .", "true", [], id="2>=2"),
        pytest.param("3 2 >= .", "true", [], id="3>=2"),
        pytest.param("2 3 != .", "true", [], id="2!=3"),
        pytest.param("2 2 != .", "false", [], id="2!=2"),
    ],
)
def test_int(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    check_aaa_main(code, expected_output, expected_exception_types)

from typing import List, Type

import pytest

from tests.aaa_code import check_aaa_code


@pytest.mark.parametrize(
    ["code", "expected_output", "expected_exception_types"],
    [
        pytest.param("nop", "", [], id="nop"),
        pytest.param("1 . // 2 .\n3 .", "13", [], id="comment"),
        pytest.param("true assert", "", [], id="assert-true"),
        pytest.param(
            "false assert",
            "",
            [NotImplementedError],
            id="assert-false",
            marks=pytest.mark.skip,
        ),
    ],
)
def test_misc(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    check_aaa_code(code, expected_output, expected_exception_types)

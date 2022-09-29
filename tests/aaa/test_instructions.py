from typing import List, Type

import pytest

from tests.aaa import check_aaa_main


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
        pytest.param("1 drop", "", [], id="drop"),
        pytest.param("1 dup . .", "11", [], id="dup"),
        pytest.param("1 2 swap . .", "12", [], id="swap"),
        pytest.param("1 2 over . . .", "121", [], id="over"),
        pytest.param("1 2 3 rot . . .", "132", [], id="rot"),
    ],
)
def test_instructions(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    check_aaa_main(code, expected_output, expected_exception_types)

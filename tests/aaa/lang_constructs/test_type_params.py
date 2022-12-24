from typing import List, Type

import pytest

from tests.aaa import check_aaa_full_source


@pytest.mark.parametrize(
    ["code", "expected_output", "expected_exception_types"],
    [
        pytest.param(
            """
            fn main { foo[int] dup 5 vec:push . }
            fn foo[A] return vec[A] { vec[A] }
            """,
            "[5]",
            [],
            id="function",
            marks=pytest.mark.skip,
        ),
        pytest.param(
            """
            fn main { foo[int] "x" ? . }
            struct foo[A] { x as A }
            """,
            "0",
            [],
            id="struct",
            marks=pytest.mark.skip,
        ),
    ],
)
def test_type_params(
    code: str,
    expected_output: str,
    expected_exception_types: List[Type[Exception]],
) -> None:
    check_aaa_full_source(code, expected_output, expected_exception_types)

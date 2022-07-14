from typing import List, Type

import pytest

from lang.typing.exceptions import MainFunctionNotFound
from tests.aaa_code import check_aaa_full_source


@pytest.mark.parametrize(
    ["code", "expected_output", "expected_exception_types"],
    [
        pytest.param(
            "fn main { 1 print } fn print args a as int { a . }",
            "1",
            [],
            id="one-param",
        ),
        pytest.param(
            "fn main { 1 2 3 print_three }\n"
            + "fn print_three args a as int, b as int, c as int { a . b . c . }",
            "123",
            [],
            id="three-params",
        ),
        pytest.param(
            "fn main { foo }\n"
            + "fn foo { bar }\n"
            + "fn bar { baz }\n"
            + "fn baz { 1 . }",
            "1",
            [],
            id="forwarding-one-param",
        ),
        pytest.param(
            "fn main { 1 2 3 foo }\n"
            + "fn foo args a as int, b as int, c as int { a b c bar }\n"
            + "fn bar args a as int, b as int, c as int { a b c baz }\n"
            + "fn baz args a as int, b as int, c as int { a . b . c . }",
            "123",
            [],
            id="forwarding-three-params",
        ),
        pytest.param(
            "fn foo { nop }",
            "",
            [MainFunctionNotFound],
            id="no-main",
            marks=pytest.mark.skip,
        ),
    ],
)
def test_function_call(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    check_aaa_full_source(code, expected_output, expected_exception_types)

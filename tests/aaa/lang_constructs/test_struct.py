from typing import List, Type

import pytest

from aaa.type_checker.exceptions import StackTypesError
from tests.aaa import check_aaa_full_source


@pytest.mark.parametrize(
    ["code", "expected_output", "expected_exception_types"],
    [
        pytest.param(
            'struct foo { x as int } fn main { foo "x" ? . drop }',
            "0",
            [],
            id="zero-value-int",
        ),
        pytest.param(
            'struct foo { x as bool } fn main { foo "x" ? . drop }',
            "false",
            [],
            id="zero-value-bool",
        ),
        pytest.param(
            'struct foo { x as str } fn main { foo "x" ? . drop }',
            "",
            [],
            id="zero-value-str",
        ),
        pytest.param(
            'struct foo { x as vec[int] } fn main { foo "x" ? . drop }',
            "[]",
            [],
            id="zero-value-vec",
        ),
        pytest.param(
            'struct foo { x as map[int, str] } fn main { foo "x" ? . drop }',
            "{}",
            [],
            id="zero-value-map",
        ),
        pytest.param(
            'struct foo { x as int } fn main { foo "x" { 3 } ! "x" ? . drop }',
            "3",
            [],
            id="set-get-int",
        ),
        pytest.param(
            'struct foo { x as bool } fn main { foo "x" { true } ! "x" ? . drop }',
            "true",
            [],
            id="set-get-bool",
        ),
        pytest.param(
            'struct foo { x as str } fn main { foo "x" { "bar" } ! "x" ? . drop }',
            "bar",
            [],
            id="set-get-str",
        ),
        pytest.param(
            'struct foo { x as vec[int] } fn main { foo "x" ? 5 vec:push "x" ? . drop }',
            "[5]",
            [],
            id="set-get-vec",
        ),
        pytest.param(
            'struct foo { x as map[int, str] } fn main { foo "x" ? 5 "five" map:set drop "x" ? . drop }',
            '{5: "five"}',
            [],
            id="set-get-map",
        ),
        pytest.param(
            'fn main { "x" ? }',
            "",
            [StackTypesError],
            id="get-stack-underflow",
        ),
        pytest.param(
            'fn main { "x" { 3 } ! }',
            "",
            [StackTypesError],
            id="set-stack-underflow",
        ),
    ],
)
def test_struct(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    check_aaa_full_source(code, expected_output, expected_exception_types)

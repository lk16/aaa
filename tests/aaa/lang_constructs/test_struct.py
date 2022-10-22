from typing import List, Type

import pytest

from aaa.type_checker.exceptions import StackTypesError
from tests.aaa import check_aaa_full_source


@pytest.mark.parametrize(
    ["code", "expected_output", "expected_exception_types"],
    [
        pytest.param(
            'struct foo { x as int } fn main { foo "x" ? . }',
            "0",
            [],
            id="zero-value-int",
        ),
        pytest.param(
            'struct foo { x as bool } fn main { foo "x" ? . }',
            "false",
            [],
            id="zero-value-bool",
        ),
        pytest.param(
            'struct foo { x as str } fn main { foo "x" ? . }',
            "",
            [],
            id="zero-value-str",
        ),
        pytest.param(
            'struct foo { x as vec[int] } fn main { foo "x" ? . }',
            "[]",
            [],
            id="zero-value-vec",
        ),
        pytest.param(
            'struct foo { x as map[int, str] } fn main { foo "x" ? . }',
            "{}",
            [],
            id="zero-value-map",
        ),
        pytest.param(
            'struct foo { x as int } fn main { foo dup "x" { 3 } ! "x" ? . }',
            "3",
            [],
            id="set-get-int",
        ),
        pytest.param(
            'struct foo { x as bool } fn main { foo dup "x" { true } ! "x" ? . }',
            "true",
            [],
            id="set-get-bool",
        ),
        pytest.param(
            'struct foo { x as str } fn main { foo dup "x" { "bar" } ! "x" ? . }',
            "bar",
            [],
            id="set-get-str",
        ),
        pytest.param(
            'struct foo { x as vec[int] } fn main { foo dup "x" ? 5 vec:push "x" ? . }',
            "[5]",
            [],
            id="set-get-vec",
        ),
        pytest.param(
            'struct foo { x as map[int, str] } fn main { foo dup "x" ? 5 "five" map:set "x" ? . }',
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

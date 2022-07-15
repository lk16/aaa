import pytest

from tests.aaa import check_aaa_full_source


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        pytest.param(
            'struct foo { x as int } fn main { foo "x" ? . drop }',
            "0",
            id="zero-value-int",
        ),
        pytest.param(
            'struct foo { x as bool } fn main { foo "x" ? . drop }',
            "false",
            id="zero-value-bool",
        ),
        pytest.param(
            'struct foo { x as str } fn main { foo "x" ? . drop }',
            "",
            id="zero-value-str",
        ),
        pytest.param(
            'struct foo { x as vec[int] } fn main { foo "x" ? . drop }',
            "[]",
            id="zero-value-vec",
        ),
        pytest.param(
            'struct foo { x as map[int, str] } fn main { foo "x" ? . drop }',
            "{}",
            id="zero-value-map",
        ),
        pytest.param(
            'struct foo { x as int } fn main { foo "x" { 3 } ! "x" ? . drop }',
            "3",
            id="set-get-int",
        ),
        pytest.param(
            'struct foo { x as bool } fn main { foo "x" { true } ! "x" ? . drop }',
            "true",
            id="set-get-bool",
        ),
        pytest.param(
            'struct foo { x as str } fn main { foo "x" { "bar" } ! "x" ? . drop }',
            "bar",
            id="set-get-str",
        ),
        pytest.param(
            'struct foo { x as vec[int] } fn main { foo "x" ? 5 vec:push drop "x" ? . drop }',
            "[5]",
            id="set-get-vec",
        ),
        pytest.param(
            'struct foo { x as map[int, str] } fn main { foo "x" ? 5 "five" map:set drop "x" ? . drop }',
            '{5: "five"}',
            id="set-get-map",
        ),
    ],
)
def test_struct(code: str, expected_output: str) -> None:
    check_aaa_full_source(code, expected_output, [])

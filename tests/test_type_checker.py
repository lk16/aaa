import pytest

from lang.parse import parse
from lang.typing.checker import TypeChecker


@pytest.mark.parametrize(
    ["code"],
    [
        ("fn main begin nop end",),
    ],
)
def test_type_checker_ok(code: str) -> None:
    root = parse("foo.txt", code)
    function = root.functions["main"]
    TypeChecker(function).check_types()

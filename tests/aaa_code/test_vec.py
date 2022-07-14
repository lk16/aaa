from typing import List, Type

import pytest

from tests.aaa_code import check_aaa_main


@pytest.mark.parametrize(
    ["code", "expected_output", "expected_exception_types"],
    [
        pytest.param("vec[int] .", "[]", [], id="print-zero-items"),
        pytest.param("vec[int] 1 vec:push .", "[1]", [], id="print-one-item"),
        pytest.param(
            "vec[int] 1 vec:push 2 vec:push .", "[1, 2]", [], id="print-two-items"
        ),
        pytest.param("vec[vec[int]] .", "[]", [], id="print-nested-zero-items"),
        pytest.param(
            "vec[vec[int]] vec[int] vec:push .", "[[]]", [], id="print-nested-one-item"
        ),
        pytest.param('vec[int] 5 vec:push vec:pop . " " . .', "5 []", [], id="pop-ok"),
        pytest.param(
            "vec[int] vec:pop . drop",
            "",
            [NotImplementedError],
            id="pop-fail",
            marks=pytest.mark.skip,
        ),
        pytest.param(
            'vec[int] 5 vec:push 0 vec:get . " " . .', "5 [5]", [], id="get-ok"
        ),
        pytest.param(
            'vec[int] 5 vec:push 1 vec:get . " " . .',
            "5 [5]",
            [NotImplementedError],
            id="get-fail",
            marks=pytest.mark.skip,
        ),
        pytest.param(
            'vec[int] 5 vec:push 0 7 vec:set vec:pop . " " . .', "7 []", [], id="set-ok"
        ),
        pytest.param(
            'vec[int] 5 vec:push 1 7 vec:set vec:pop . " " . .',
            "7 []",
            [NotImplementedError],
            id="set-fail",
            marks=pytest.mark.skip,
        ),
        pytest.param("vec[int] vec:size . drop", "0", [], id="size-zero-items"),
        pytest.param(
            "vec[int] 5 vec:push vec:size . drop", "1", [], id="size-one-item"
        ),
        pytest.param(
            "vec[int] 5 vec:push vec:empty . drop", "false", [], id="empty-false"
        ),
        pytest.param("vec[int] vec:empty . drop", "true", [], id="empty-true"),
        pytest.param("vec[int] 5 vec:push vec:clear .", "[]", [], id="clear"),
        pytest.param(
            "vec[int] 5 vec:push vec:copy vec:clear vec:size . drop vec:size . drop",
            "01",
            [],
            id="copy",
        ),
        pytest.param(
            "vec[int] 5 vec:push dup vec:clear vec:size . drop vec:size . drop",
            "00",
            [],
            id="dup",
        ),
        pytest.param(
            "vec[vec[int]] vec[int] 5 vec:push vec:push .",
            "[[5]]",
            [],
            id="nested-one-item",
        ),
    ],
)
def test_vec(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    check_aaa_main(code, expected_output, expected_exception_types)

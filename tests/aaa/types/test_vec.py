from typing import List, Type

import pytest

from tests.aaa import check_aaa_main


@pytest.mark.parametrize(
    ["code", "expected_output", "expected_exception_types"],
    [
        pytest.param("vec[int] .", "[]", [], id="print-zero-items"),
        pytest.param("vec[int] dup 1 vec:push .", "[1]", [], id="print-one-item"),
        pytest.param(
            "vec[int] dup 1 vec:push dup 2 vec:push .",
            "[1, 2]",
            [],
            id="print-two-items",
        ),
        pytest.param("vec[vec[int]] .", "[]", [], id="print-nested-zero-items"),
        pytest.param(
            "vec[vec[int]] dup vec[int] vec:push .",
            "[[]]",
            [],
            id="print-nested-one-item",
        ),
        pytest.param(
            'vec[int] dup 5 vec:push dup vec:pop . " " . .', "5 []", [], id="pop-ok"
        ),
        pytest.param(
            "vec[int] dup vec:pop . drop",
            "",
            [NotImplementedError],
            id="pop-fail",
            marks=pytest.mark.skip,
        ),
        pytest.param(
            'vec[int] dup 5 vec:push dup 0 vec:get . " " . .', "5 [5]", [], id="get-ok"
        ),
        pytest.param(
            'vec[int] dup 5 vec:push dup 1 vec:get . " " . .',
            "5 [5]",
            [NotImplementedError],
            id="get-fail",
            marks=pytest.mark.skip,
        ),
        pytest.param(
            'vec[int] dup 5 vec:push dup 0 7 vec:set dup vec:pop . " " . .',
            "7 []",
            [],
            id="set-ok",
        ),
        pytest.param(
            'vec[int] 5 vec:push 1 7 vec:set vec:pop . " " . .',
            "7 []",
            [NotImplementedError],
            id="set-fail",
            marks=pytest.mark.skip,
        ),
        pytest.param("vec[int] vec:size .", "0", [], id="size-zero-items"),
        pytest.param("vec[int] dup 5 vec:push vec:size .", "1", [], id="size-one-item"),
        pytest.param(
            "vec[int] dup 5 vec:push vec:empty .", "false", [], id="empty-false"
        ),
        pytest.param("vec[int] vec:empty .", "true", [], id="empty-true"),
        pytest.param("vec[int] dup 5 vec:push dup vec:clear .", "[]", [], id="clear"),
        pytest.param(
            "vec[int] dup 5 vec:push dup vec:copy dup vec:clear vec:size . vec:size .",
            "01",
            [],
            id="copy",
        ),
        pytest.param(
            "vec[int] dup 5 vec:push dup dup vec:clear vec:size . vec:size .",
            "00",
            [],
            id="dup",
        ),
        pytest.param(
            "vec[vec[int]] dup vec[int] dup 5 vec:push vec:push .",
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

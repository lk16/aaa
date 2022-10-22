from typing import List, Type

import pytest

from tests.aaa import check_aaa_main


@pytest.mark.parametrize(
    ["code", "expected_output", "expected_exception_types"],
    [
        pytest.param("map[int, int] .", "{}", [], id="print-zero-items"),
        pytest.param("map[int, map[int, int]] .", "{}", [], id="print-nested"),
        pytest.param(
            'map[str, int] dup "one" 1 map:set .', '{"one": 1}', [], id="print-one-item"
        ),
        pytest.param(
            'map[str, int] dup "one" 1 map:set "one" map:get .', "1", [], id="get-set"
        ),
        pytest.param(
            'map[str, int] dup "one" 1 map:set dup "one" 2 map:set "one" map:get .',
            "2",
            [],
            id="get-set-update",
        ),
        pytest.param(
            'map[str, int] dup "one" map:get drop',
            "",
            [NotImplementedError],
            id="get-fail",
            marks=pytest.mark.skip,
        ),
        pytest.param(
            'map[str, int] dup "one" 1 map:set "one" map:has_key .',
            "true",
            [],
            id="has_key-true",
        ),
        pytest.param(
            'map[str, int] dup "one" 1 map:set "two" map:has_key .',
            "false",
            [],
            id="has_key-false",
        ),
        pytest.param(
            'map[str, int] dup "one" 1 map:set map:size .', "1", [], id="size-one-item"
        ),
        pytest.param("map[str, int] map:size .", "0", [], id="size-zero-items"),
        pytest.param(
            'map[str, int] dup "one" 1 map:set map:empty .',
            "false",
            [],
            id="empty-false",
        ),
        pytest.param("map[str, int] map:empty .", "true", [], id="empty-true"),
        pytest.param(
            'map[str, int] dup "one" 1 map:set dup map:clear map:size .',
            "0",
            [],
            id="clear",
        ),
        pytest.param(
            'map[str, int] dup "one" 1 map:set dup map:copy dup map:clear map:size . map:size .',
            "01",
            [],
            id="copy",
        ),
        pytest.param(
            'map[str, int] dup "one" 1 map:set dup map:clear dup map:size . map:size .',
            "00",
            [],
            id="dup",
        ),
        pytest.param(
            'map[str, int] dup "one" 1 map:set "one" map:pop .',
            "1",
            [],
            id="pop-ok",
        ),
        pytest.param(
            'map[str, int] dup "one" map:pop .',
            "",
            [NotImplementedError],
            id="pop-fail",
            marks=pytest.mark.skip,
        ),
        pytest.param(
            'map[str, int] dup "one" 1 map:set dup "one" map:drop .',
            "{}",
            [],
            id="drop-ok",
        ),
    ],
)
def test_map(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    check_aaa_main(code, expected_output, expected_exception_types)

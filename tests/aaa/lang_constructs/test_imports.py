from typing import Dict, List, Type

import pytest

from lang.exceptions.import_ import ImportedItemNotFound
from lang.parse.exceptions import FileReadError
from tests.aaa import check_aaa_full_source_multi_file


@pytest.mark.parametrize(
    ["files", "expected_output", "expected_exception_types"],
    [
        pytest.param(
            {
                "add.aaa": "fn add args a as int, b as int, return int, { a b + }",
                "main.aaa": 'from "add" import add,\n fn main { 3 2 add . }',
            },
            "5",
            [],
            id="two-files",
        ),
        pytest.param(
            {
                "add.aaa": "fn add args a as int, b as int, return int, { a b + }",
                "main.aaa": 'from "add" import add as foo,\n fn main { 3 2 foo . }',
            },
            "5",
            [],
            id="two-files-alias",
        ),
        pytest.param(
            {
                "add.aaa": "fn add args a as int, b as int, return int, { a b + }",
                "main.aaa": 'from "add" import foo,\n fn main { 3 2 foo . }',
            },
            "5",
            [ImportedItemNotFound],
            id="two-files-nonexistent-function",
        ),
        pytest.param(
            {
                "main.aaa": 'from "add" import add,\n fn main { 3 2 add . }',
            },
            "5",
            [FileReadError],
            id="two-files-nonexistent-file",
        ),
        pytest.param(
            {
                "five.aaa": "fn five return int { 5 }",
                "six.aaa": 'from "five" import five\n fn six return int { five 1 + }',
                "main.aaa": 'from "six" import six\n fn main { six . }',
            },
            "6",
            [],
            id="three-files",
        ),
    ],
)
def test_imports(
    files: Dict[str, str],
    expected_output: str,
    expected_exception_types: List[Type[Exception]],
) -> None:
    check_aaa_full_source_multi_file(files, expected_output, expected_exception_types)

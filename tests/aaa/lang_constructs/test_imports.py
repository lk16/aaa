from pathlib import Path
from typing import Dict, List, Type

import pytest

from aaa.cross_referencer.exceptions import ImportedItemNotFound
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
            [Exception],
            id="two-files-nonexistent-file",
            marks=pytest.mark.skip,  # TODO
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
    file_dict = {Path(file): code for file, code in files.items()}
    check_aaa_full_source_multi_file(
        file_dict, expected_output, expected_exception_types
    )

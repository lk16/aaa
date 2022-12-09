from glob import glob
from pathlib import Path

import pytest

from aaa.tokenizer.tokenizer import Tokenizer


@pytest.mark.parametrize(
    ["file"],
    [
        pytest.param(Path(file_name), id=file_name)
        for file_name in glob("**/*.aaa", root_dir=".", recursive=True)
    ],
)
def test_tokenizer_parts_add_up(file: Path) -> None:
    tokens = Tokenizer(file).tokenize_unfiltered()

    tokens_concatenated = "".join(token.value for token in tokens)
    assert tokens_concatenated == file.read_text()


# TODO add tests for various token types

# TODO add tokenizer exceptions and tests for all those cases

from glob import glob
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir

import pytest

from aaa.tokenizer.models import TokenType
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


@pytest.mark.parametrize(
    ["code", "expected_token_type"],
    [
        pytest.param(" ", TokenType.WHITESPACE, id="space"),
        pytest.param("\n", TokenType.WHITESPACE, id="newline"),
        pytest.param("\t", TokenType.WHITESPACE, id="tab"),
        pytest.param(" \t\n \t\n", TokenType.WHITESPACE, id="mixed_whitespace"),
        pytest.param("fn", TokenType.FUNCTION, id="fixed_size"),
        pytest.param(">=", TokenType.OPERATOR, id="fixed_size_with_shorter_substring"),
        pytest.param("// comment", TokenType.COMMENT, id="comment"),
        pytest.param("#!/usr/bin/env aaa", TokenType.SHEBANG, id="shebang"),
        pytest.param("123", TokenType.INTEGER, id="positive_integer"),
        pytest.param("-123", TokenType.INTEGER, id="negative_integer"),
        pytest.param("AaBb_YyZz", TokenType.IDENTIFIER, id="identifier"),
        pytest.param('""', TokenType.STRING, id="string_empty"),
        pytest.param('"hello"', TokenType.STRING, id="string_simple"),
        pytest.param(
            '"\\n \\\\ \\""', TokenType.STRING, id="string_with_escape_sequences"
        ),
    ],
)
def test_tokenizer_token_types(code: str, expected_token_type: TokenType) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)
    tokens = Tokenizer(file).tokenize_unfiltered()

    assert 1 == len(tokens)
    assert expected_token_type == tokens[0].type
    assert code == tokens[0].value


# TODO add tokenizer exceptions and tests for all those cases

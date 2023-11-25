from glob import glob
from pathlib import Path

import pytest

from aaa import aaa_project_root
from aaa.parser.lib.exceptions import TokenizerException
from aaa.parser.lib.file_parser import FileParser
from aaa.parser.parser import SYNTAX_JSON_PATH

file_parser = FileParser(SYNTAX_JSON_PATH)


@pytest.mark.parametrize(
    ["file"],
    [
        pytest.param(Path(file_name), id=file_name)
        for file_name in glob("**/*.aaa", root_dir=aaa_project_root(), recursive=True)
    ],
)
def test_tokenizer_parts_add_up(file: Path) -> None:
    # TODO this test should be moved into parser lib, since it's not specific to Aaa
    tokens = file_parser.tokenize_file(file, filter_token_types=False)

    tokens_concatenated = "".join(token.value for token in tokens)
    assert tokens_concatenated == file.read_text()


@pytest.mark.parametrize(
    ["code", "expected_token_type"],
    [
        pytest.param(" ", "whitespace", id="space"),
        pytest.param("\n", "whitespace", id="newline"),
        pytest.param("\t", "whitespace", id="tab"),
        pytest.param(" \t\n \t\n", "whitespace", id="mixed_whitespace"),
        pytest.param("fn", "fn", id="fixed_size"),
        pytest.param(">=", "identifier", id="fixed_size_with_shorter_substring"),
        pytest.param("// comment", "comment", id="comment"),
        pytest.param("123", "integer", id="positive_integer"),
        pytest.param("-123", "integer", id="negative_integer"),
        pytest.param("AaBb_YyZz", "identifier", id="identifier"),
        pytest.param('""', "string", id="string_empty"),
        pytest.param('"hello"', "string", id="string_simple"),
        pytest.param('"\\n \\\\ \\""', "string", id="string_with_escape_sequences"),
    ],
)
def test_tokenizer_token_types(code: str, expected_token_type: str) -> None:
    # TODO use same testing as in test_parser.py and make sure we test all token types
    tokens = file_parser.tokenize_text(code, filter_token_types=False)

    assert 1 == len(tokens)
    assert expected_token_type == tokens[0].type
    assert code == tokens[0].value


@pytest.mark.parametrize(
    ["code", "expected_line", "expected_column"],
    [
        pytest.param(' fn "', 1, 5, id="string_without_end"),
        pytest.param(' fn "\n"', 1, 5, id="string_with_unprintable_char"),
        pytest.param(' fn "\\y', 1, 5, id="string_with_invalid_escape_sequence"),
        pytest.param(' fn "\\', 1, 5, id="string_with_half_escape_sequence"),
        pytest.param("~", 1, 1, id="unknown_sequence"),
    ],
)
def test_tokenizer_error(code: str, expected_line: int, expected_column: int) -> None:
    with pytest.raises(TokenizerException) as e:
        file_parser.tokenize_text(code)

    tokenizer_exception = e.value

    assert expected_line == tokenizer_exception.position.line
    assert expected_column == tokenizer_exception.position.column


# TODO move test_character_literal_regex() to parse tests

# TODO mvoe test_string_literal_regex() to parse tests

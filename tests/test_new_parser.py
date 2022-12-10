from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir
from typing import List, Type

import pytest

from aaa.parser.exceptions import (
    NewParserEndOfFileException,
    NewParserException,
    ParserBaseException,
)
from aaa.parser.new_parser import SingleFileParser
from aaa.tokenizer.tokenizer import Tokenizer


@pytest.mark.parametrize(
    ["code", "expected"],
    [
        ("abc_def", "abc_def"),
        ("Abc_deF", "Abc_deF"),
        ("_", "_"),
        ("", NewParserEndOfFileException),
        ("3", NewParserException),
    ],
)
def test_parse_identifier(
    code: str,
    expected: str | Type[ParserBaseException],
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if isinstance(expected, str):
        identifier, offset = parser._parse_identifier(0)
        assert 1 == offset
        assert expected == identifier.name
    else:
        with pytest.raises(expected):
            parser._parse_identifier(0)


@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("[", NewParserException, 0),
        ("[A", NewParserException, 0),
        ("[]", NewParserException, 0),
        ("[A]", ["A"], 3),
        ("[A,", NewParserException, 0),
        ("[A,]", NewParserException, 0),
        ("[A,B", NewParserException, 0),
        ("[A,B]", ["A", "B"], 5),
        ("[A,B,C]", ["A", "B", "C"], 7),
        ("[ A , B , C ]", ["A", "B", "C"], 7),
        ("", NewParserEndOfFileException, 0),
        ("3", NewParserException, 0),
    ],
)
def test_parse_flat_type_params(
    code: str,
    expected_result: List[str] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if isinstance(expected_result, list):
        type_params, offset = parser._parser_flat_type_params(0)
        assert expected_offset == offset
        assert expected_result == [
            type_param.identifier.name for type_param in type_params
        ]
    else:
        with pytest.raises(expected_result):
            parser._parse_identifier(0)

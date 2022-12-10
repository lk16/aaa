from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir
from typing import List, Tuple, Type

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
        ("[", NewParserEndOfFileException, 0),
        ("[A", NewParserEndOfFileException, 0),
        ("[]", NewParserException, 0),
        ("[A]", ["A"], 3),
        ("[A,", NewParserEndOfFileException, 0),
        ("[A,]", NewParserException, 0),
        ("[,A]", NewParserException, 0),
        ("[A,B", NewParserEndOfFileException, 0),
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
        type_params, offset = parser._parse_flat_type_params(0)
        assert expected_offset == offset
        assert expected_result == [
            type_param.identifier.name for type_param in type_params
        ]
    else:
        with pytest.raises(expected_result):
            parser._parse_flat_type_params(0)


@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("foo[", ("foo", []), 1),
        ("foo[A", ("foo", []), 1),
        ("foo[]", ("foo", []), 1),
        ("foo", ("foo", []), 1),
        ("foo[A]", ("foo", ["A"]), 4),
        ("foo[A,", ("foo", []), 1),
        ("foo[A,]", ("foo", []), 1),
        ("foo[A,B", ("foo", []), 1),
        ("foo[A,B]", ("foo", ["A", "B"]), 6),
        ("foo[A,B,C]", ("foo", ["A", "B", "C"]), 8),
        ("", NewParserEndOfFileException, 0),
        ("3", NewParserException, 0),
    ],
)
def test_parse_flat_type_literal(
    code: str,
    expected_result: Tuple[str, List[str]] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if isinstance(expected_result, tuple):
        type_literal, offset = parser._parse_flat_type_literal(0)
        expected_type_name, expected_type_params = expected_result

        assert expected_offset == offset
        assert expected_type_name == type_literal.identifier.name
        assert expected_type_params == [
            type_param.identifier.name for type_param in type_literal.params
        ]
    else:
        with pytest.raises(expected_result):
            parser._parse_flat_type_literal(0)


@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("type foo[", ("foo", []), 2),
        ("type foo[A", ("foo", []), 2),
        ("type foo[]", ("foo", []), 2),
        ("type foo", ("foo", []), 2),
        ("type foo[A]", ("foo", ["A"]), 5),
        ("type foo[A,", ("foo", []), 2),
        ("type foo[A,]", ("foo", []), 2),
        ("type foo[A,B", ("foo", []), 2),
        ("type foo[A,B]", ("foo", ["A", "B"]), 7),
        ("type foo[A,B,C]", ("foo", ["A", "B", "C"]), 9),
        ("", NewParserEndOfFileException, 0),
        ("3", NewParserException, 0),
    ],
)
def test_parse_type_declaration(
    code: str,
    expected_result: Tuple[str, List[str]] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if isinstance(expected_result, tuple):
        type_literal, offset = parser._parse_type_declaration(0)
        expected_type_name, expected_type_params = expected_result

        assert expected_offset == offset
        assert expected_type_name == type_literal.identifier.name
        assert expected_type_params == [
            type_param.identifier.name for type_param in type_literal.params
        ]
    else:
        with pytest.raises(expected_result):
            parser._parse_type_declaration(0)

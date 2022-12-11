from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir
from typing import List, Optional, Tuple, Type

import pytest

from aaa.parser.exceptions import (
    NewParserEndOfFileException,
    NewParserException,
    ParserBaseException,
)
from aaa.parser.new_parser import SingleFileParser
from aaa.parser.parser import Parser
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
        ("[A,]", ["A"], 4),
        ("[,A]", NewParserException, 0),
        ("[A,B", NewParserEndOfFileException, 0),
        ("[A,B]", ["A", "B"], 5),
        ("[A,B,]", ["A", "B"], 6),
        ("[A,B,C]", ["A", "B", "C"], 7),
        ("[A,B,C,]", ["A", "B", "C"], 8),
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
        ("foo[A[B]]", ("foo", []), 1),
        ("foo[A,", ("foo", []), 1),
        ("foo[A,]", ("foo", ["A"]), 5),
        ("foo[A,B", ("foo", []), 1),
        ("foo[A,B]", ("foo", ["A", "B"]), 6),
        ("foo[A,B,]", ("foo", ["A", "B"]), 7),
        ("foo[A,B,C]", ("foo", ["A", "B", "C"]), 8),
        ("foo[A,B,C,]", ("foo", ["A", "B", "C"]), 9),
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
        ("type foo[A,]", ("foo", ["A"]), 6),
        ("type foo[A,B", ("foo", []), 2),
        ("type foo[A,B]", ("foo", ["A", "B"]), 7),
        ("type foo[A,B,]", ("foo", ["A", "B"]), 8),
        ("type foo[A,B,C]", ("foo", ["A", "B", "C"]), 9),
        ("type foo[A,B,C,]", ("foo", ["A", "B", "C"]), 10),
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


@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("foo", (None, [], "foo"), 1),
        ("foo[", (None, [], "foo"), 1),
        ("foo[]", (None, [], "foo"), 1),
        ("foo:", NewParserEndOfFileException, 0),
        ("foo[]:", (None, [], "foo"), 1),
        ("foo:bar", ("foo", [], "bar"), 3),
        ("foo[A]", (None, ["A"], "foo"), 4),
        ("foo[A,]", (None, ["A"], "foo"), 5),
        ("foo[A,B]", (None, ["A", "B"], "foo"), 6),
        ("foo[A,B,]", (None, ["A", "B"], "foo"), 7),
        ("foo[A,B,C]", (None, ["A", "B", "C"], "foo"), 8),
        ("foo[A,B,C,]", (None, ["A", "B", "C"], "foo"), 9),
        ("foo[A]:bar", ("foo", ["A"], "bar"), 6),
        ("foo[A,]:bar", ("foo", ["A"], "bar"), 7),
        ("foo[A,B]:bar", ("foo", ["A", "B"], "bar"), 8),
        ("foo[A,B,]:bar", ("foo", ["A", "B"], "bar"), 9),
        ("foo[A,B,C]:bar", ("foo", ["A", "B", "C"], "bar"), 10),
        ("foo[A,B,C,]:bar", ("foo", ["A", "B", "C"], "bar"), 11),
        ("", NewParserEndOfFileException, 0),
        ("3", NewParserException, 0),
    ],
)
def test_parse_function_name(
    code: str,
    expected_result: Tuple[str, List[str], Optional[str]] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if isinstance(expected_result, tuple):
        function_name, offset = parser._parse_function_name(0)
        expected_struct_name, expected_type_params, expected_func_name = expected_result

        assert expected_offset == offset

        if expected_struct_name is not None:
            assert function_name.struct_name
            assert expected_struct_name == function_name.struct_name.name
        else:
            assert function_name.struct_name is None

        assert expected_func_name == function_name.func_name.name
        assert expected_type_params == [
            param.identifier.name for param in function_name.type_params
        ]
    else:
        with pytest.raises(expected_result):
            parser._parse_function_name(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("[]", NewParserException, 0),
        ("[A]", None, 3),
        ("[A", NewParserEndOfFileException, 0),
        ("[A,", NewParserEndOfFileException, 0),
        ("[A,]", None, 4),
        ("[,", NewParserException, 0),
        ("[A,B]", None, 5),
        ("[A,B,]", None, 6),
        ("[A[B]]", None, 6),
        ("[A[B,]]", None, 7),
        ("[[A]B]", NewParserException, 0),
        ("[A[B],C]", None, 8),
        ("[A[B[C]],D]", None, 11),
        ("", NewParserEndOfFileException, 0),
        ("3", NewParserException, 0),
    ],
)
def test_parse_type_params(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if expected_exception is None:
        _, offset = parser._parse_type_params(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_type_params(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("foo", None, 1),
        ("foo[]", None, 1),
        ("[A]", NewParserException, 0),
        ("foo[A]", None, 4),
        ("foo[A", None, 1),
        ("foo[A,", None, 1),
        ("foo[A,]", None, 5),
        ("foo[,", None, 1),
        ("foo[A,B]", None, 6),
        ("foo[A,B,]", None, 7),
        ("foo[A[B]]", None, 7),
        ("foo[A[B,]]", None, 8),
        ("foo[A[B,],]", None, 9),
        ("foo[[A]B]", None, 1),
        ("foo[A[B],C]", None, 9),
        ("foo[A[B[C]],D]", None, 12),
        ("", NewParserEndOfFileException, 0),
        ("3", NewParserException, 0),
    ],
)
def test_parse_type_literal(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if expected_exception is None:
        _, offset = parser._parse_type_literal(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_type_literal(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("foo", NewParserEndOfFileException, 0),
        ("foo as", NewParserEndOfFileException, 0),
        ("foo as bar", None, 3),
        ("foo as bar[]", None, 3),
        ("foo as bar[A", None, 3),
        ("foo as bar[", None, 3),
        ("foo as bar[A]", None, 6),
        ("foo as bar[A,]", None, 7),
        ("foo as bar[A,B]", None, 8),
        ("foo as bar[A,B,]", None, 9),
        ("", NewParserEndOfFileException, 0),
        ("3", NewParserException, 0),
    ],
)
def test_parse_argument(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if expected_exception is None:
        _, offset = parser._parse_argument(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_argument(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("foo", NewParserEndOfFileException, 0),
        ("foo as", NewParserEndOfFileException, 0),
        ("foo as bar", None, 3),
        ("foo as bar[A]", None, 6),
        ("foo as bar[A,B]", None, 8),
        ("foo as bar[A,B],", None, 9),
        ("foo as bar[A,B],foo as bar[A,B]", None, 17),
        ("foo as bar[A,B],foo as bar[A,B],", None, 18),
        ("", NewParserEndOfFileException, 0),
        ("3", NewParserException, 0),
    ],
)
def test_parse_arguments(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if expected_exception is None:
        _, offset = parser._parse_arguments(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_arguments(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("foo", None, 1),
        ("foo,", None, 2),
        ("foo[A]", None, 4),
        ("foo[A],", None, 5),
        ("foo[A,B]", None, 6),
        ("foo[A,B],", None, 7),
        ("foo[A,B],foo[A,B]", None, 13),
        ("foo[A,B],foo[A,B],", None, 14),
        ("", NewParserEndOfFileException, 0),
        ("3", NewParserException, 0),
    ],
)
def test_parse_return_types(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if expected_exception is None:
        _, offset = parser._parse_return_types(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_return_types(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("fn a", None, 2),
        ("fn a,", None, 2),
        ("fn a args b as int", None, 6),
        ("fn a args b as int,", None, 7),
        ("fn a args b as int, c as int", None, 10),
        ("fn a args b as int, c as int,", None, 11),
        ("fn a args b as vec[int], c as vec[int],", None, 17),
        ("fn a args b as vec[int,], c as vec[int,],", None, 19),
        ("fn a return int", None, 4),
        ("fn a return int,", None, 5),
        ("fn a return vec[int]", None, 7),
        ("fn a return vec[int],map[int,int]", None, 14),
        ("fn a return vec[int],map[int,int],", None, 15),
        ("fn a return vec[int],map[int,vec[int]],", None, 18),
        ("fn a args b as vec[int], return vec[int],map[int,vec[int]],", None, 26),
        ("fn a args", NewParserEndOfFileException, 0),
        ("fn a return", NewParserEndOfFileException, 0),
        ("fn a return", NewParserEndOfFileException, 0),
        ("fn a return vec[", None, 4),
        ("", NewParserEndOfFileException, 0),
        ("3", NewParserException, 0),
    ],
)
def test_parse_function_declaration(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if expected_exception is None:
        _, offset = parser._parse_function_declaration(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_function_declaration(0)


def test_parse_builtins_file() -> None:
    file = Path("./stdlib/builtins.aaa")

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    parsed_file, offset = parser._parse_builtins_file_root(0)
    assert len(tokens) == offset

    old_parser = Parser(Path("."), file, None)
    expected_parsed_file = old_parser._parse(file, old_parser._get_builtins_parser())

    assert expected_parsed_file.types == parsed_file.types
    assert expected_parsed_file.functions == parsed_file.functions


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("", None, 0),
        ("fn a", None, 2),
        ("fn a fn b", None, 4),
        ("type a", None, 2),
        ("type a type b", None, 4),
        ("type a[A,B] fn a args b as vec[int,map[int,int]] return c", None, 25),
        ("3", None, 0),
    ],
)
def test_parse_builtins_root(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if expected_exception is None:
        _, offset = parser._parse_builtins_file_root(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_builtins_file_root(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("struct a", NewParserEndOfFileException, 0),
        ("struct a {", NewParserEndOfFileException, 0),
        ("struct a {}", NewParserException, 0),
        ("struct a { b as int }", None, 7),
        ("struct a { b as int, }", None, 8),
        ("struct a { b as map[int,vec[int]] }", None, 15),
        ("struct a { b as map[int,vec[int]], }", None, 16),
        ("struct a { b as int, }", None, 8),
        ("struct a { b as int, c as int }", None, 11),
        ("struct a { b as int, c as int, }", None, 12),
        ("", NewParserEndOfFileException, 0),
        ("3", NewParserException, 0),
    ],
)
def test_parse_struct_definition(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if expected_exception is None:
        _, offset = parser._parse_struct_definition(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_struct_definition(0)


@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ('""', "", 1),
        ('"foo"', "foo", 1),
        ('"\\n"', "\n", 1),
        ('"\\r"', "\r", 1),
        ('"\\\\"', "\\", 1),
        ('"\\""', '"', 1),
        ("", NewParserEndOfFileException, 0),
        ("3", NewParserException, 0),
    ],
)
def test_parse_string(
    code: str,
    expected_result: str | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if isinstance(expected_result, str):
        string, offset = parser._parse_string(0)
        assert expected_offset == offset
        assert expected_result == string.value
    else:
        with pytest.raises(expected_result):
            parser._parse_string(0)


@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("foo", ("foo", "foo"), 1),
        ("foo as", NewParserEndOfFileException, 0),
        ("foo as bar", ("foo", "bar"), 3),
        ("", NewParserEndOfFileException, 0),
        ("3", NewParserException, 0),
    ],
)
def test_parse_import_item(
    code: str,
    expected_result: Tuple[str, str] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    temp_file = NamedTemporaryFile(delete=False)
    file = Path(gettempdir()) / temp_file.name

    file.write_text(code)

    tokens = Tokenizer(file).run()
    parser = SingleFileParser(file, tokens)

    if isinstance(expected_result, tuple):
        expected_original_name, expected_imported_name = expected_result

        import_item, offset = parser._parse_import_item(0)
        assert expected_original_name == import_item.original_name
        assert expected_imported_name == import_item.imported_name
        assert expected_offset == offset
    else:
        with pytest.raises(expected_result):
            parser._parse_import_item(0)

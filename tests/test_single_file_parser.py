from glob import glob
from pathlib import Path
from typing import List, Optional, Set, Tuple, Type

import pytest

from aaa import aaa_project_root, create_test_output_folder
from aaa.parser.exceptions import (
    EndOfFileException,
    ParserBaseException,
    ParserException,
    UnhandledTopLevelToken,
)
from aaa.parser.models import FlatTypeLiteral, FunctionPointerTypeLiteral, TypeLiteral
from aaa.parser.single_file_parser import SingleFileParser
from aaa.tokenizer.tokenizer import Tokenizer


def parse_code(code: str) -> SingleFileParser:
    file = create_test_output_folder() / "sample.aaa"

    file.write_text(code)

    tokens = Tokenizer(file, False).run()
    return SingleFileParser(file, tokens, False)


@pytest.mark.parametrize(
    ["code", "expected"],
    [
        ("abc_def", "abc_def"),
        ("Abc_deF", "Abc_deF"),
        ("_", "_"),
        ("", EndOfFileException),
        ("3", ParserException),
    ],
)
def test_parse_identifier(
    code: str,
    expected: str | Type[ParserBaseException],
) -> None:
    parser = parse_code(code)

    if isinstance(expected, str):
        identifier, offset = parser._parse_identifier(0)
        assert 1 == offset
        assert expected == identifier.name
    else:
        with pytest.raises(expected):
            parser._parse_identifier(0)


def get_type_param_variable_type_names(
    type_params: List[FlatTypeLiteral | FunctionPointerTypeLiteral]
    | List[FlatTypeLiteral]
    | List[TypeLiteral | FunctionPointerTypeLiteral],
) -> List[str]:
    names: List[str] = []

    for type_param in type_params:
        assert isinstance(type_param, (TypeLiteral, FlatTypeLiteral))
        names.append(type_param.identifier.name)

    return names


@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("[", EndOfFileException, 0),
        ("[A", EndOfFileException, 0),
        ("[]", ParserException, 0),
        ("[A]", ["A"], 3),
        ("[A,", EndOfFileException, 0),
        ("[A,]", ["A"], 4),
        ("[,A]", ParserException, 0),
        ("[A,B", EndOfFileException, 0),
        ("[A,B]", ["A", "B"], 5),
        ("[A,B,]", ["A", "B"], 6),
        ("[A,B,C]", ["A", "B", "C"], 7),
        ("[A,B,C,]", ["A", "B", "C"], 8),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_flat_type_params(
    code: str,
    expected_result: List[str] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if isinstance(expected_result, list):
        type_params, offset = parser._parse_flat_type_params(0)
        assert expected_offset == offset
        assert expected_result == get_type_param_variable_type_names(type_params)
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
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_flat_type_literal(
    code: str,
    expected_result: Tuple[str, List[str]] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if isinstance(expected_result, tuple):
        type_literal, offset = parser._parse_flat_type_literal(0)
        expected_type_name, expected_type_params = expected_result

        assert expected_offset == offset
        assert expected_type_name == type_literal.identifier.name
        assert expected_type_params == get_type_param_variable_type_names(
            type_literal.params
        )
    else:
        with pytest.raises(expected_result):
            parser._parse_flat_type_literal(0)


@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("struct foo[", ("foo", []), 2),
        ("struct foo[A", ("foo", []), 2),
        ("struct foo[]", ("foo", []), 2),
        ("struct foo", ("foo", []), 2),
        ("struct foo[A]", ("foo", ["A"]), 5),
        ("struct foo[A,", ("foo", []), 2),
        ("struct foo[A,]", ("foo", ["A"]), 6),
        ("struct foo[A,B", ("foo", []), 2),
        ("struct foo[A,B]", ("foo", ["A", "B"]), 7),
        ("struct foo[A,B,]", ("foo", ["A", "B"]), 8),
        ("struct foo[A,B,C]", ("foo", ["A", "B", "C"]), 9),
        ("struct foo[A,B,C,]", ("foo", ["A", "B", "C"]), 10),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_struct_declaration(
    code: str,
    expected_result: Tuple[str, List[str]] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if isinstance(expected_result, tuple):
        type_literal, offset = parser._parse_struct_declaration(0)
        expected_type_name, expected_type_params = expected_result

        assert expected_offset == offset
        assert expected_type_name == type_literal.identifier.name
        assert expected_type_params == get_type_param_variable_type_names(
            type_literal.params
        )
    else:
        with pytest.raises(expected_result):
            parser._parse_type_declaration(0)


@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("foo", (None, [], "foo"), 1),
        ("foo[", (None, [], "foo"), 1),
        ("foo[]", (None, [], "foo"), 1),
        ("foo:", EndOfFileException, 0),
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
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_function_name(
    code: str,
    expected_result: Tuple[str, List[str], Optional[str]] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

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
        assert expected_type_params == get_type_param_variable_type_names(
            function_name.type_params
        )
    else:
        with pytest.raises(expected_result):
            parser._parse_function_name(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("[]", ParserException, 0),
        ("[A]", None, 3),
        ("[A", EndOfFileException, 0),
        ("[A,", EndOfFileException, 0),
        ("[A,]", None, 4),
        ("[,", ParserException, 0),
        ("[A,B]", None, 5),
        ("[A,B,]", None, 6),
        ("[A[B]]", None, 6),
        ("[A[B,]]", None, 7),
        ("[[A]B]", ParserException, 0),
        ("[A[B],C]", None, 8),
        ("[A[B[C]],D]", None, 11),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_type_params(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

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
        ("const foo", None, 2),
        ("foo[]", None, 1),
        ("[A]", ParserException, 0),
        ("foo[A]", None, 4),
        ("const foo[A]", None, 5),
        ("foo[const A]", None, 5),
        ("foo[A", None, 1),
        ("foo[A,", None, 1),
        ("foo[A,]", None, 5),
        ("foo[,", None, 1),
        ("foo[A,B]", None, 6),
        ("foo[const A,B]", None, 7),
        ("foo[A,B,]", None, 7),
        ("foo[A[B]]", None, 7),
        ("foo[A[B,]]", None, 8),
        ("foo[A[B,],]", None, 9),
        ("foo[[A]B]", None, 1),
        ("foo[A[B],C]", None, 9),
        ("foo[A[B[C]],D]", None, 12),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_type_literal(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_type_literal(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_type_literal(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("foo", EndOfFileException, 0),
        ("foo as", EndOfFileException, 0),
        ("foo as bar", None, 3),
        ("foo as bar[]", None, 3),
        ("foo as bar[A", None, 3),
        ("foo as bar[", None, 3),
        ("foo as bar[A]", None, 6),
        ("foo as bar[A,]", None, 7),
        ("foo as bar[A,B]", None, 8),
        ("foo as bar[A,B,]", None, 9),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_argument(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_argument(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_argument(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("foo", EndOfFileException, 0),
        ("foo as", EndOfFileException, 0),
        ("foo as bar", None, 3),
        ("foo as bar[A]", None, 6),
        ("foo as bar[A,B]", None, 8),
        ("foo as bar[A,B],", None, 9),
        ("foo as bar[A,B],foo as bar[A,B]", None, 17),
        ("foo as bar[A,B],foo as bar[A,B],", None, 18),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_arguments(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

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
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_return_types(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

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
        ("fn a args", EndOfFileException, 0),
        ("fn a return", EndOfFileException, 0),
        ("fn a return", EndOfFileException, 0),
        ("fn a return vec[", None, 4),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_function_declaration(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_function_declaration(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_function_declaration(0)


def test_parse_builtins_file_root() -> None:
    file = Path("./stdlib/builtins.aaa")

    tokens = Tokenizer(file, False).run()
    parser = SingleFileParser(file, tokens, False)

    parsed_file, offset = parser._parse_builtins_file_root(0)
    assert len(tokens) == offset


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("", None, 0),
        ("fn a", None, 2),
        ("fn a fn b", None, 4),
        ("struct a", None, 2),
        ("struct a struct b", None, 4),
        ("struct a[A,B] fn a args b as vec[int,map[int,int]] return c", None, 25),
        ("3", None, 0),
    ],
)
def test_parse_builtins_root(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_builtins_file_root(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_builtins_file_root(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("struct a", EndOfFileException, 0),
        ("struct a {", EndOfFileException, 0),
        ("struct a {}", None, 4),
        ("struct a { b as int }", None, 7),
        ("struct a { b as int, }", None, 8),
        ("struct a { b as map[int,vec[int]] }", None, 15),
        ("struct a { b as map[int,vec[int]], }", None, 16),
        ("struct a { b as int, }", None, 8),
        ("struct a { b as int, c as int }", None, 11),
        ("struct a { b as int, c as int, }", None, 12),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_struct_definition(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

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
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_string(
    code: str,
    expected_result: str | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

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
        ("foo as", EndOfFileException, 0),
        ("foo as bar", ("foo", "bar"), 3),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_import_item(
    code: str,
    expected_result: Tuple[str, str] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if isinstance(expected_result, tuple):
        expected_original_name, expected_imported_name = expected_result

        import_item, offset = parser._parse_import_item(0)
        assert expected_original_name == import_item.original.name
        assert expected_imported_name == import_item.imported.name
        assert expected_offset == offset
    else:
        with pytest.raises(expected_result):
            parser._parse_import_item(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("foo", None, 1),
        ("foo,", None, 2),
        ("foo,bar", None, 3),
        ("foo,bar,", None, 4),
        ("foo as bar,foo", None, 5),
        ("foo as bar,foo,", None, 6),
        ("foo,foo as bar", None, 5),
        ("foo,foo as bar,", None, 6),
        ("foo as", EndOfFileException, 0),
        ("foo as bar", None, 3),
        ("foo as bar,", None, 4),
        ("foo as bar,foo", None, 5),
        ("foo as bar,foo as", None, 4),
        ("foo as bar,foo as bar", None, 7),
        ("foo as bar,foo as bar,", None, 8),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_import_items(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_import_items(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_import_items(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("from", EndOfFileException, 0),
        ('from "a"', EndOfFileException, 0),
        ('from "a" import', EndOfFileException, 0),
        ("from a import b", ParserException, 0),
        ('from "a" import b', None, 4),
        ('from "a" import b,', None, 5),
        ('from "a" import b as c', None, 6),
        ('from "a" import b as c,', None, 7),
        ('from "a" import b as c,d', None, 8),
        ('from "a" import b as c,d,', None, 9),
        ('from "a" import b as c,d as e', None, 10),
        ('from "a" import b as c,d as e,', None, 11),
        ('from "a" import b,d as e,', None, 9),
        ('from "a" import b as c,d,', None, 9),
        ('from "a" import b,d,', None, 7),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_import_statement(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_import_statement(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_import_statement(0)


@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("true", True, 1),
        ("false", False, 1),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_boolean(
    code: str,
    expected_result: bool | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if isinstance(expected_result, bool):
        boolean, offset = parser._parse_boolean(0)
        assert expected_result == boolean.value
        assert expected_offset == offset
    else:
        with pytest.raises(expected_result):
            parser._parse_boolean(0)


@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("0", 0, 1),
        ("123", 123, 1),
        ("-456", -456, 1),
        ("", EndOfFileException, 0),
        ("true", ParserException, 0),
    ],
)
def test_parse_integer(
    code: str,
    expected_result: int | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if isinstance(expected_result, int):
        boolean, offset = parser._parse_integer(0)
        assert expected_result == boolean.value
        assert expected_offset == offset
    else:
        with pytest.raises(expected_result):
            parser._parse_integer(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("0", None, 1),
        ("123", None, 1),
        ("-456", None, 1),
        ("true", None, 1),
        ("false", None, 1),
        ('"foo"', None, 1),
        ("case", ParserException, 0),
        ("", EndOfFileException, 0),
    ],
)
def test_parse_literal(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if not expected_exception:
        _, offset = parser._parse_function_body_item(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_function_body_item(0)


@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("foo", (None, [], "foo"), 1),
        ("foo[A]", (None, ["A"], "foo"), 4),
        ("foo[A,]", (None, ["A"], "foo"), 5),
        ("foo[A,B]", (None, ["A", "B"], "foo"), 6),
        ("foo[A,B,]", (None, ["A", "B"], "foo"), 7),
        ("foo:bar", ("foo", [], "bar"), 3),
        ("fn", ParserException, 0),
        ("", EndOfFileException, 0),
    ],
)
def test_parse_function_call(
    code: str,
    expected_result: Tuple[Optional[str], List[str], str] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if isinstance(expected_result, tuple):
        expected_struct_name, expected_type_params, expected_func_name = expected_result
        func_call, offset = parser._parse_function_call(0)

        if expected_struct_name is not None:
            assert func_call.struct_name
            assert expected_struct_name == func_call.struct_name.name
        else:
            assert expected_struct_name is None

        assert expected_type_params == get_type_param_variable_type_names(
            func_call.type_params
        )
        assert expected_func_name == func_call.func_name.name

        assert expected_offset == offset
    else:
        with pytest.raises(expected_result):
            parser._parse_function_call(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("if", EndOfFileException, 0),
        ("if true", EndOfFileException, 0),
        ("if true {", EndOfFileException, 0),
        ("if true { nop", EndOfFileException, 0),
        ("if true { nop } else ", EndOfFileException, 0),
        ("if true { nop } else {", EndOfFileException, 0),
        ("if true { nop } else { nop", EndOfFileException, 0),
        ("if true { nop }", None, 5),
        ("if true { nop } else { nop }", None, 9),
        ("if true { while true { nop } }", None, 9),
        ("if true { if true { nop } else { nop } }", None, 13),
        ('if true { "x" ? }', None, 6),
        ('if true { "x" { nop } ! }', None, 9),
        ('if true { "x" }', None, 5),
        ('if true { "x" 3 }', None, 6),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_branch(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_branch(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_branch(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("while", EndOfFileException, 0),
        ("while true", EndOfFileException, 0),
        ("while true {", EndOfFileException, 0),
        ("while true { nop", EndOfFileException, 0),
        ("while true { nop }", None, 5),
        ("while true { while true { nop } }", None, 9),
        ("while true { if true { nop } else { nop } }", None, 13),
        ('while true { "x" ? }', None, 6),
        ('while true { "x" { nop } ! }', None, 9),
        ('while true { "x" }', None, 5),
        ('while true { "x" 3 }', None, 6),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_loop(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_while_loop(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_while_loop(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ('"foo"', EndOfFileException, 0),
        ('"foo" ?', None, 2),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_field_query(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_struct_field_query(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_struct_field_query(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ('"foo"', EndOfFileException, 0),
        ('"foo" {', EndOfFileException, 0),
        ('"foo" { nop', EndOfFileException, 0),
        ('"foo" { nop }', EndOfFileException, 0),
        ('"foo" { nop } !', None, 5),
        ('"foo" { while true { nop } } !', None, 9),
        ('"foo" { if true { nop } else { nop } } !', None, 13),
        ('"foo" { "x" ? } !', None, 6),
        ('"foo" { "x" { nop } ! } !', None, 9),
        ('"foo" { "x" } !', None, 5),
        ('"foo" { "x" 3 } !', None, 6),
        ("", EndOfFileException, 0),
        ("3", ParserException, 0),
    ],
)
def test_parse_struct_field_update(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_struct_field_update(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_struct_field_update(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("3", None, 1),
        ("false", None, 1),
        ('"foo"', None, 1),
        ("foo", None, 1),
        ("foo[A]", None, 4),
        ("foo[A,]", None, 5),
        ("foo[A,B]", None, 6),
        ("foo[A,B,]", None, 7),
        ("foo:bar", None, 3),
        ("if true { nop }", None, 5),
        ("if true { nop } else { nop }", None, 9),
        ("while true { nop }", None, 5),
        ('"foo" ?', None, 2),
        ('"foo" { nop } !', None, 5),
        ("", EndOfFileException, 0),
        ("case", ParserException, 0),
    ],
)
def test_parse_function_body_item(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_function_body_item(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_function_body_item(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("3", None, 1),
        ("false", None, 1),
        ('"foo"', None, 1),
        ("foo", None, 1),
        ("foo[A]", None, 4),
        ("foo[A,]", None, 5),
        ("foo[A,B]", None, 6),
        ("foo[A,B,]", None, 7),
        ("foo:bar", None, 3),
        ("if true { nop }", None, 5),
        ("if true { nop } else { nop }", None, 9),
        ("while true { nop }", None, 5),
        ('"foo" ?', None, 2),
        ('"foo" { nop } !', None, 5),
        ("if true { nop } 3", None, 6),
        ("if true { nop } false", None, 6),
        ('if true { nop } "foo"', None, 6),
        ("if true { nop } foo", None, 6),
        ("if true { nop } foo[A]", None, 9),
        ("if true { nop } foo[A,]", None, 10),
        ("if true { nop } foo[A,B]", None, 11),
        ("if true { nop } foo[A,B,]", None, 12),
        ("if true { nop } foo:bar", None, 8),
        ("if true { nop } if true { nop }", None, 10),
        ("if true { nop } if true { nop } else { nop }", None, 14),
        ("if true { nop } while true { nop }", None, 10),
        ('if true { nop } "foo" ?', None, 7),
        ('if true { nop } "foo" { nop } !', None, 10),
        ("", EndOfFileException, 0),
        ("case", ParserException, 0),
    ],
)
def test_parse_function_body(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_function_body(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_function_body(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("fn", EndOfFileException, 0),
        ("fn foo", EndOfFileException, 0),
        ("fn foo {", EndOfFileException, 0),
        ("fn foo { nop", EndOfFileException, 0),
        ("fn foo { nop }", None, 5),
        ("fn foo args a as int { nop }", None, 9),
        ("fn foo args a as vec[map[int,str]] { nop }", None, 17),
        ("fn foo args a as vec[map[int,str]] { while true { nop } }", None, 21),
        ("3", ParserException, 0),
    ],
)
def test_parse_function_definition(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_function_definition(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_function_definition(0)


def test_parse_regular_file_root_empty_file() -> None:
    file = create_test_output_folder() / "sample.aaa"
    file.write_text("")

    tokens = Tokenizer(file, False).run()
    parser = SingleFileParser(file, tokens, False)

    _, offset = parser._parse_regular_file_root(0)
    assert 0 == offset


def get_source_files() -> List[Path]:
    aaa_files: Set[Path] = {
        Path(file)
        for file in glob("**/*.aaa", root_dir=aaa_project_root(), recursive=True)
    }
    builtins_file = Path("./stdlib/builtins.aaa")
    return sorted(aaa_files - {builtins_file})


@pytest.mark.parametrize(
    ["file"],
    [pytest.param(file, id=str(file)) for file in get_source_files()],
)
def test_parse_regular_file_all_source_files(file: Path) -> None:
    tokens = Tokenizer(file, False).run()
    parser = SingleFileParser(file, tokens, False)

    parser.parse_regular_file()


def test_parse_builtins_file() -> None:
    file = Path("./stdlib/builtins.aaa")
    tokens = Tokenizer(file, False).run()
    parser = SingleFileParser(file, tokens, False)

    parser.parse_builtins_file()


def test_parse_regular_file_fail() -> None:
    code = "fn foo { nop } 3"

    parser = parse_code(code)

    with pytest.raises(UnhandledTopLevelToken):
        parser.parse_regular_file()


def test_parse_builtins_file_fail() -> None:
    code = "fn foo args a as int return bool 3"

    parser = parse_code(code)

    with pytest.raises(UnhandledTopLevelToken):
        parser.parse_builtins_file()


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("a", None, 1),
        ("a,", None, 2),
        ("a,b", None, 3),
        ("a,b,", None, 4),
        ("a,b,c", None, 5),
        ("a,b,c,", None, 6),
        ("3", ParserException, 0),
    ],
)
def test_parse_variables(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_variables(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_variables(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("use { nop } ", ParserException, 0),
        ("use a { nop } ", None, 5),
        ("use a, { nop } ", None, 6),
        ("use a,b { nop } ", None, 7),
        ("use a,b, { nop } ", None, 8),
        ("use a,b,c { nop } ", None, 9),
        ("use a,b,c, { nop } ", None, 10),
        ("3", ParserException, 0),
    ],
)
def test_parse_use_block(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_use_block(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_use_block(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("<- { nop } ", ParserException, 0),
        ("a <- { nop } ", None, 5),
        ("a, <- { nop } ", None, 6),
        ("a,b <- { nop } ", None, 7),
        ("a,b, <- { nop } ", None, 8),
        ("a,b,c <- { nop } ", None, 9),
        ("a,b,c, <- { nop } ", None, 10),
        ("3", ParserException, 0),
    ],
)
def test_parse_assignment(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_assignment(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_assignment(0)


@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("fn[][]", None, 5),
        ("fn [][]", None, 5),
        ("fn[ ][]", None, 5),
        ("fn[] []", None, 5),
        ("fn[][ ]", None, 5),
        ("fn[int][]", None, 6),
        ("fn[int,][]", None, 7),
        ("fn[][int]", None, 6),
        ("fn[vec[int]][]", None, 9),
        ("fn[int,int][]", None, 8),
        ("fn[int,int,][]", None, 9),
        ("fn[][int,int]", None, 8),
        ("fn[][int,int,]", None, 9),
        ("fn[fn[][]][]", None, 10),
        ("fn[,][]", ParserException, 0),
        ("fn[][,]", ParserException, 0),
    ],
)
def test_parse_function_pointer_type_literal(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    parser = parse_code(code)

    if expected_exception is None:
        _, offset = parser._parse_function_pointer_type_literal(0)
        assert expected_offset == offset
    else:
        with pytest.raises(expected_exception):
            parser._parse_assignment(0)


@pytest.mark.parametrize(
    ["code"],
    [
        (
            "// foo\n",  # fmt: skip
        ),
        (
            "// foo\n"  # fmt: skip
            "fn main { nop }\n",
        ),
        (
            "fn main { nop }\n"  # fmt: skip
            "// foo\n",
        ),
    ],
)
def test_parse_comment_in_regular_file(code: str) -> None:
    parser = parse_code(code)
    parser.parse_regular_file()


@pytest.mark.parametrize(
    ["code"],
    [
        (
            "fn main {\n"  # fmt: skip
            "    // foo\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    // foo\n"
            "    nop\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    nop\n"
            "    // foo\n"
            "}\n",
        ),
    ],
)
def test_parse_comment_in_function_body(code: str) -> None:
    parser = parse_code(code)
    parser.parse_regular_file()


@pytest.mark.parametrize(
    ["code"],
    [
        (
            "fn main {\n"  # fmt: skip
            "    // foo\n"
            "    while 1 2 { nop }\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    while\n"
            "    // foo\n"
            "    1 2 { nop }\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    while 1 2\n"
            "    // foo\n"
            "    { nop }\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    while 1 2 {\n"
            "    // foo\n"
            "    nop }\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    while 1 2 { nop\n"
            "    // foo\n"
            "    }\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    while 1 2 { nop }\n"
            "    // foo\n"
            "}\n",
        ),
    ],
)
def test_parse_comment_in_while_loop(code: str) -> None:
    parser = parse_code(code)
    parser.parse_regular_file()


@pytest.mark.parametrize(
    ["code"],
    [
        (
            "fn main {\n"  # fmt: skip
            "    // foo\n"
            "    if true { nop } else { nop }\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    if \n"
            "    // foo\n"
            "    true { nop } else { nop }\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    if true \n"
            "    // foo\n"
            "    { nop } else { nop }\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    if true {\n"
            "    // foo\n"
            "    nop } else { nop }\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    if true { nop\n"
            "    // foo\n"
            "    } else { nop }\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    if true { nop }\n"
            "    // foo\n"
            "    else { nop }\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    if true { nop } else\n"
            "    // foo\n"
            "    { nop }\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    if true { nop } else {\n"
            "    // foo\n"
            "    nop }\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    if true { nop } else { nop\n"
            "    // foo\n"
            "    }\n"
            "}\n",
        ),
        (
            "fn main {\n"  # fmt: skip
            "    if true { nop } else { nop }\n"
            "    // foo\n"
            "}\n",
        ),
    ],
)
def test_parse_comment_in_branch(code: str) -> None:
    parser = parse_code(code)
    parser.parse_regular_file()


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_struct_field_query(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_struct_field_update(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_get_function_pointer(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_return(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_call(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_argument(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_function(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_import_item(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_import(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_struct(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_parsed_file(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_type_literal(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_function_pointer_type_literal(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_function_name(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_function_call(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_case_label(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_foreach_loop(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_use_block(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_assignment(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_case_block(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_default_block(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_match_block(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_enum_variant(code: str) -> None:
    ...


@pytest.mark.skip
@pytest.mark.parametrize(
    ["code"],
    [],
)
def test_parse_comment_in_enum(code: str) -> None:
    ...

from glob import glob
from pathlib import Path
from typing import List, Optional, Set, Tuple, Type

import pytest

from aaa import aaa_project_root, get_stdlib_path
from aaa.parser.lib.exceptions import (
    EndOfFile,
    ParserBaseException,
    UnexpectedTokenType,
)
from aaa.parser.models import (
    FlatTypeLiteral,
    FlatTypeParams,
    FunctionPointerTypeLiteral,
    TypeLiteral,
)
from aaa.parser.parser import AaaParser


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
    ["code", "expected_result"],
    [
        ("[", EndOfFile),
        ("[A", EndOfFile),
        ("[]", UnexpectedTokenType),
        ("[A]", ["A"]),
        ("[A,", EndOfFile),
        ("[A,]", ["A"]),
        ("[,A]", UnexpectedTokenType),
        ("[A,B", EndOfFile),
        ("[A,B]", ["A", "B"]),
        ("[A,B,]", ["A", "B"]),
        ("[A,B,C]", ["A", "B", "C"]),
        ("[A,B,C,]", ["A", "B", "C"]),
        ("", EndOfFile),
        ("3", UnexpectedTokenType),
    ],
)
def test_parse_flat_type_params(
    code: str,
    expected_result: List[str] | Type[ParserBaseException],
) -> None:
    try:
        flat_type_params = AaaParser(False).parse_text(code, "FLAT_TYPE_PARAMS")
    except Exception as e:
        assert isinstance(expected_result, type)
        assert isinstance(e, expected_result)
    else:
        assert isinstance(flat_type_params, FlatTypeParams)
        assert expected_result == [item.name for item in flat_type_params.value]


@pytest.mark.parametrize(
    ["code", "expected_result"],
    [
        ("foo[", UnexpectedTokenType),
        ("foo[A", UnexpectedTokenType),
        ("foo[]", UnexpectedTokenType),
        ("foo", ("foo", [])),
        ("foo[A]", ("foo", ["A"])),
        ("foo[A[B]]", UnexpectedTokenType),
        ("foo[A,", UnexpectedTokenType),
        ("foo[A,]", ("foo", ["A"])),
        ("foo[A,B", UnexpectedTokenType),
        ("foo[A,B]", ("foo", ["A", "B"])),
        ("foo[A,B,]", ("foo", ["A", "B"])),
        ("foo[A,B,C", UnexpectedTokenType),
        ("foo[A,B,C]", ("foo", ["A", "B", "C"])),
        ("foo[A,B,C,]", ("foo", ["A", "B", "C"])),
        ("", EndOfFile),
        ("3", UnexpectedTokenType),
    ],
)
def test_parse_flat_type_literal(
    code: str,
    expected_result: Tuple[str, List[str]] | Type[ParserBaseException],
) -> None:
    try:
        flat_type_literal = AaaParser(False).parse_text(code, "FLAT_TYPE_LITERAL")
    except Exception as e:
        assert isinstance(expected_result, type)
        assert isinstance(e, expected_result)
    else:
        assert isinstance(flat_type_literal, FlatTypeLiteral)
        assert isinstance(expected_result, tuple)
        expected_name, expected_param_names = expected_result
        assert expected_name == flat_type_literal.identifier.name
        assert expected_param_names == [item.name for item in flat_type_literal.params]


@pytest.mark.skip()  # TODO
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
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_struct_declaration(
    code: str,
    expected_result: Tuple[str, List[str]] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("foo", (None, [], "foo"), 1),
        ("foo[", (None, [], "foo"), 1),
        ("foo[]", (None, [], "foo"), 1),
        ("foo:", EndOfFile, 0),
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
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_function_name(
    code: str,
    expected_result: Tuple[str, List[str], Optional[str]] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("[]", UnexpectedTokenType, 0),
        ("[A]", None, 3),
        ("[A", EndOfFile, 0),
        ("[A,", EndOfFile, 0),
        ("[A,]", None, 4),
        ("[,", UnexpectedTokenType, 0),
        ("[A,B]", None, 5),
        ("[A,B,]", None, 6),
        ("[A[B]]", None, 6),
        ("[A[B,]]", None, 7),
        ("[[A]B]", UnexpectedTokenType, 0),
        ("[A[B],C]", None, 8),
        ("[A[B[C]],D]", None, 11),
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_type_params(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("foo", None, 1),
        ("const foo", None, 2),
        ("foo[]", None, 1),
        ("[A]", UnexpectedTokenType, 0),
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
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_type_literal(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("foo", EndOfFile, 0),
        ("foo as", EndOfFile, 0),
        ("foo as bar", None, 3),
        ("foo as bar[]", None, 3),
        ("foo as bar[A", None, 3),
        ("foo as bar[", None, 3),
        ("foo as bar[A]", None, 6),
        ("foo as bar[A,]", None, 7),
        ("foo as bar[A,B]", None, 8),
        ("foo as bar[A,B,]", None, 9),
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_argument(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("foo", EndOfFile, 0),
        ("foo as", EndOfFile, 0),
        ("foo as bar", None, 3),
        ("foo as bar[A]", None, 6),
        ("foo as bar[A,B]", None, 8),
        ("foo as bar[A,B],", None, 9),
        ("foo as bar[A,B],foo as bar[A,B]", None, 17),
        ("foo as bar[A,B],foo as bar[A,B],", None, 18),
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_arguments(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
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
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_return_types(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
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
        ("fn a args", EndOfFile, 0),
        ("fn a return", EndOfFile, 0),
        ("fn a return", EndOfFile, 0),
        ("fn a return vec[", None, 4),
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_function_declaration(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


def test_parse_builtins_file_root() -> None:
    file = get_stdlib_path() / "builtins.aaa"
    AaaParser(False).parse_file(file)


@pytest.mark.skip()  # TODO
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
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("struct a", EndOfFile, 0),
        ("struct a {", EndOfFile, 0),
        ("struct a {}", None, 4),
        ("struct a { b as int }", None, 7),
        ("struct a { b as int, }", None, 8),
        ("struct a { b as map[int,vec[int]] }", None, 15),
        ("struct a { b as map[int,vec[int]], }", None, 16),
        ("struct a { b as int, }", None, 8),
        ("struct a { b as int, c as int }", None, 11),
        ("struct a { b as int, c as int, }", None, 12),
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_struct_definition(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ('""', "", 1),
        ('"foo"', "foo", 1),
        ('"\\n"', "\n", 1),
        ('"\\r"', "\r", 1),
        ('"\\\\"', "\\", 1),
        ('"\\""', '"', 1),
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_string(
    code: str,
    expected_result: str | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("foo", ("foo", "foo"), 1),
        ("foo as", EndOfFile, 0),
        ("foo as bar", ("foo", "bar"), 3),
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_import_item(
    code: str,
    expected_result: Tuple[str, str] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
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
        ("foo as", EndOfFile, 0),
        ("foo as bar", None, 3),
        ("foo as bar,", None, 4),
        ("foo as bar,foo", None, 5),
        ("foo as bar,foo as", None, 4),
        ("foo as bar,foo as bar", None, 7),
        ("foo as bar,foo as bar,", None, 8),
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_import_items(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("from", EndOfFile, 0),
        ('from "a"', EndOfFile, 0),
        ('from "a" import', EndOfFile, 0),
        ("from a import b", UnexpectedTokenType, 0),
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
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_import_statement(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("true", True, 1),
        ("false", False, 1),
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_boolean(
    code: str,
    expected_result: bool | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("0", 0, 1),
        ("123", 123, 1),
        ("-456", -456, 1),
        ("", EndOfFile, 0),
        ("true", UnexpectedTokenType, 0),
    ],
)
def test_parse_integer(
    code: str,
    expected_result: int | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("0", None, 1),
        ("123", None, 1),
        ("-456", None, 1),
        ("true", None, 1),
        ("false", None, 1),
        ('"foo"', None, 1),
        ("case", UnexpectedTokenType, 0),
        ("", EndOfFile, 0),
    ],
)
def test_parse_literal(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_result", "expected_offset"],
    [
        ("foo", (None, [], "foo"), 1),
        ("foo[A]", (None, ["A"], "foo"), 4),
        ("foo[A,]", (None, ["A"], "foo"), 5),
        ("foo[A,B]", (None, ["A", "B"], "foo"), 6),
        ("foo[A,B,]", (None, ["A", "B"], "foo"), 7),
        ("foo:bar", ("foo", [], "bar"), 3),
        ("fn", UnexpectedTokenType, 0),
        ("", EndOfFile, 0),
    ],
)
def test_parse_function_call(
    code: str,
    expected_result: Tuple[Optional[str], List[str], str] | Type[ParserBaseException],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("if", EndOfFile, 0),
        ("if true", EndOfFile, 0),
        ("if true {", EndOfFile, 0),
        ("if true { nop", EndOfFile, 0),
        ("if true { nop } else ", EndOfFile, 0),
        ("if true { nop } else {", EndOfFile, 0),
        ("if true { nop } else { nop", EndOfFile, 0),
        ("if true { nop }", None, 5),
        ("if true { nop } else { nop }", None, 9),
        ("if true { while true { nop } }", None, 9),
        ("if true { if true { nop } else { nop } }", None, 13),
        ('if true { "x" ? }', None, 6),
        ('if true { "x" { nop } ! }', None, 9),
        ('if true { "x" }', None, 5),
        ('if true { "x" 3 }', None, 6),
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_branch(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("while", EndOfFile, 0),
        ("while true", EndOfFile, 0),
        ("while true {", EndOfFile, 0),
        ("while true { nop", EndOfFile, 0),
        ("while true { nop }", None, 5),
        ("while true { while true { nop } }", None, 9),
        ("while true { if true { nop } else { nop } }", None, 13),
        ('while true { "x" ? }', None, 6),
        ('while true { "x" { nop } ! }', None, 9),
        ('while true { "x" }', None, 5),
        ('while true { "x" 3 }', None, 6),
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_loop(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ('"foo"', EndOfFile, 0),
        ('"foo" ?', None, 2),
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_field_query(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ('"foo"', EndOfFile, 0),
        ('"foo" {', EndOfFile, 0),
        ('"foo" { nop', EndOfFile, 0),
        ('"foo" { nop }', EndOfFile, 0),
        ('"foo" { nop } !', None, 5),
        ('"foo" { while true { nop } } !', None, 9),
        ('"foo" { if true { nop } else { nop } } !', None, 13),
        ('"foo" { "x" ? } !', None, 6),
        ('"foo" { "x" { nop } ! } !', None, 9),
        ('"foo" { "x" } !', None, 5),
        ('"foo" { "x" 3 } !', None, 6),
        ("", EndOfFile, 0),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_struct_field_update(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
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
        ("", EndOfFile, 0),
        ("case", UnexpectedTokenType, 0),
    ],
)
def test_parse_function_body_item(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
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
        ("", EndOfFile, 0),
        ("case", UnexpectedTokenType, 0),
    ],
)
def test_parse_function_body(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("fn", EndOfFile, 0),
        ("fn foo", EndOfFile, 0),
        ("fn foo {", EndOfFile, 0),
        ("fn foo { nop", EndOfFile, 0),
        ("fn foo { nop }", None, 5),
        ("fn foo args a as int { nop }", None, 9),
        ("fn foo args a as vec[map[int,str]] { nop }", None, 17),
        ("fn foo args a as vec[map[int,str]] { while true { nop } }", None, 21),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_function_definition(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
def test_parse_regular_file_root_empty_file() -> None:
    raise NotImplementedError


def get_source_files() -> List[Path]:
    aaa_files: Set[Path] = {
        Path(file)
        for file in glob("**/*.aaa", root_dir=aaa_project_root(), recursive=True)
    }
    builtins_file = Path("./stdlib/builtins.aaa")
    return sorted(aaa_files - {builtins_file})


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["file"],
    [pytest.param(file, id=str(file)) for file in get_source_files()],
)
def test_parse_regular_file_all_source_files(file: Path) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
def test_parse_regular_file_fail() -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
def test_parse_builtins_file_fail() -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("a", None, 1),
        ("a,", None, 2),
        ("a,b", None, 3),
        ("a,b,", None, 4),
        ("a,b,c", None, 5),
        ("a,b,c,", None, 6),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_variables(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("use { nop } ", UnexpectedTokenType, 0),
        ("use a { nop } ", None, 5),
        ("use a, { nop } ", None, 6),
        ("use a,b { nop } ", None, 7),
        ("use a,b, { nop } ", None, 8),
        ("use a,b,c { nop } ", None, 9),
        ("use a,b,c, { nop } ", None, 10),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_use_block(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["code", "expected_exception", "expected_offset"],
    [
        ("<- { nop } ", UnexpectedTokenType, 0),
        ("a <- { nop } ", None, 5),
        ("a, <- { nop } ", None, 6),
        ("a,b <- { nop } ", None, 7),
        ("a,b, <- { nop } ", None, 8),
        ("a,b,c <- { nop } ", None, 9),
        ("a,b,c, <- { nop } ", None, 10),
        ("3", UnexpectedTokenType, 0),
    ],
)
def test_parse_assignment(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
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
        ("fn[,][]", UnexpectedTokenType, 0),
        ("fn[][,]", UnexpectedTokenType, 0),
    ],
)
def test_parse_function_pointer_type_literal(
    code: str,
    expected_exception: Optional[Type[ParserBaseException]],
    expected_offset: int,
) -> None:
    raise NotImplementedError


@pytest.mark.skip()  # TODO
@pytest.mark.parametrize(
    ["escaped", "expected_unescaped"],
    [
        ("", ""),
        ("abc", "abc"),
        ("\\\\", "\\"),
        ("a\\\\b", "a\\b"),
        ("\\\\b", "\\b"),
        ("a\\\\", "a\\"),
        ('a\\"b', 'a"b'),
        ("a\\'b", "a'b"),
        ("a\\/b", "a/b"),
        ("a\\0b", "a\0b"),
        ("a\\bb", "a\bb"),
        ("a\\eb", "a\x1bb"),
        ("a\\fb", "a\fb"),
        ("a\\nb", "a\nb"),
        ("a\\rb", "a\rb"),
        ("a\\tb", "a\tb"),
        ("a\\u0000b", "a\u0000b"),
        ("a\\u9999b", "a\u9999b"),
        ("a\\uaaaab", "a\uaaaab"),
        ("a\\uffffb", "a\uffffb"),
        ("a\\uAAAAb", "a\uaaaab"),
        ("a\\uFFFFb", "a\uffffb"),
        ("a\\U00000000b", "a\U00000000b"),
        ("a\\U0001F600b", "a\U0001F600b"),
    ],
)
def test_unescape_string(escaped: str, expected_unescaped: str) -> None:
    raise NotImplementedError

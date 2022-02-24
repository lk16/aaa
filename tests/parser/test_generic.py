import re
from enum import IntEnum, auto
from typing import Dict

import pytest

from lang.parser.generic import (
    InternalParseError,
    ParseError,
    Parser,
    RegexBasedParser,
    cat,
    lit,
    new_parse_generic,
    opt,
    rep,
    sym,
)


class TestSymbolType(IntEnum):
    PROGRAM = auto()
    A = auto()
    B = auto()
    C = auto()
    D = auto()


# shorthand to keep tests readable
T = TestSymbolType


@pytest.mark.parametrize("code", ["", "A", "B", "C", "D", "AA", "DA", "AD"])
def test_parser_three_options(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: sym(T.A) | sym(T.B) | sym(T.C),
        TestSymbolType.A: lit("A"),
        TestSymbolType.B: lit("B"),
        TestSymbolType.C: lit("C"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("A|B|C").fullmatch(code)

    try:
        new_parse_generic(rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize("code", ["", "A", "foo", "f", "B", " foo", "foo ", " foo "])
def test_parser_option_of_literal_and_symbol(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: (sym(T.A) | lit("foo")),
        TestSymbolType.A: lit("A"),
        TestSymbolType.B: lit("B"),
        TestSymbolType.C: lit("C"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("A|foo").fullmatch(code)

    try:
        new_parse_generic(rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize("code", ["", "A", "AB", "ABC", " ABC", "ABC "])
def test_parser_three_literals(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: cat(lit("A"), lit("B"), lit("C")),
        TestSymbolType.A: lit("A"),
        TestSymbolType.B: lit("B"),
        TestSymbolType.C: lit("C"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("ABC").fullmatch(code)

    try:
        new_parse_generic(rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    "code", ["A", "B", "C", "D", "AB", "AB ", "AC", "BC", "BD", "AA"]
)
def test_parser_optionals_with_concatenation(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: cat((sym(T.A) | sym(T.B)), (sym(T.C) | sym(T.D))),
        TestSymbolType.A: lit("A"),
        TestSymbolType.B: lit("B"),
        TestSymbolType.C: lit("C"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("(A|B)(C|D)").fullmatch(code)

    try:
        new_parse_generic(rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    "code", ["", "foo", "foobar", "foobarbaz", "-foobarbaz", "foobarbazquux"]
)
def test_parser_concatenate_three_symbols(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: cat(sym(T.A), sym(T.B), sym(T.C)),
        TestSymbolType.A: lit("foo"),
        TestSymbolType.B: lit("bar"),
        TestSymbolType.C: lit("baz"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("foobarbaz").fullmatch(code)

    try:
        new_parse_generic(rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize("code", ["", "A", "B", "AB", "AAB", "AAAB", "BB", "ABB"])
def test_parser_repeat_symbols(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: cat(rep(sym(T.A)), sym(T.B)),
        TestSymbolType.A: lit("A"),
        TestSymbolType.B: lit("B"),
        TestSymbolType.C: lit("C"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("A*B").fullmatch(code)

    try:
        new_parse_generic(rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize("code", ["", "A", "B", "AB", "AAB", "AAAB", "BB", "ABB"])
def test_parser_repeat_symbols_with_at_least_one(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: cat(rep(sym(T.A), m=1), sym(T.B)),
        TestSymbolType.A: lit("A"),
        TestSymbolType.B: lit("B"),
        TestSymbolType.C: lit("C"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("A+B").fullmatch(code)

    try:
        new_parse_generic(rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize("code", ["", "AC", "ABC", "ABB", "CCB", "AAA"])
def test_parser_optional_symbol(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: cat(sym(T.A), opt(sym(T.B)), sym(T.C)),
        TestSymbolType.A: lit("A"),
        TestSymbolType.B: lit("B"),
        TestSymbolType.C: lit("C"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("AB?C").fullmatch(code)

    try:
        new_parse_generic(rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType)
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


def test_flat_concatenation_expression() -> None:
    expr = cat(sym(T.A), sym(T.B), sym(T.C))
    assert len(expr.children) == 3


def test_flat_option_expression() -> None:
    expr = sym(T.A) | sym(T.B) | sym(T.C)
    assert len(expr.children) == 3


@pytest.mark.parametrize(
    ["code", "expected_match"],
    [
        ("", False),
        ("acd", True),
        ("bcd", True),
        ("acccd", True),
        ("bd", True),
        ("xacd", False),
        ("acdx", True),
    ],
)
def test_regex_parser(code: str, expected_match: bool) -> None:
    parser = RegexBasedParser("^(a|b)c*d")

    try:
        parser.parse(code, 0)
    except InternalParseError:
        assert not expected_match
    else:
        assert expected_match

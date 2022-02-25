import re
from enum import IntEnum, auto
from typing import Dict

import pytest

from lang.parser.generic import (
    ConcatenationParser,
    InternalParseError,
    LiteralParser,
    OptionalParser,
    OrParser,
    ParseError,
    Parser,
    RegexBasedParser,
    RepeatParser,
    SymbolParser,
    new_parse_generic,
)


# NOTE: Should not have Test prefix
class SymbolsForTesting(IntEnum):
    PROGRAM = auto()
    A = auto()
    B = auto()
    C = auto()
    D = auto()


@pytest.mark.parametrize("code", ["", "A", "B", "C", "D", "AA", "DA", "AD"])
def test_parser_three_options(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        SymbolsForTesting.PROGRAM: OrParser(
            SymbolParser(SymbolsForTesting.A),
            SymbolParser(SymbolsForTesting.B),
            SymbolParser(SymbolsForTesting.C),
        ),
        SymbolsForTesting.A: LiteralParser("A"),
        SymbolsForTesting.B: LiteralParser("B"),
        SymbolsForTesting.C: LiteralParser("C"),
        SymbolsForTesting.D: LiteralParser("D"),
    }

    expected_ok = re.compile("A|B|C").fullmatch(code)

    try:
        new_parse_generic(
            rewrite_rules, SymbolsForTesting.PROGRAM, code, SymbolsForTesting
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize("code", ["", "A", "foo", "f", "B", " foo", "foo ", " foo "])
def test_parser_option_of_literal_and_symbol(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        SymbolsForTesting.PROGRAM: OrParser(
            SymbolParser(SymbolsForTesting.A), LiteralParser("foo")
        ),
        SymbolsForTesting.A: LiteralParser("A"),
        SymbolsForTesting.B: LiteralParser("B"),
        SymbolsForTesting.C: LiteralParser("C"),
        SymbolsForTesting.D: LiteralParser("D"),
    }

    expected_ok = re.compile("A|foo").fullmatch(code)

    try:
        new_parse_generic(
            rewrite_rules, SymbolsForTesting.PROGRAM, code, SymbolsForTesting
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize("code", ["", "A", "AB", "ABC", " ABC", "ABC "])
def test_parser_three_literals(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        SymbolsForTesting.PROGRAM: ConcatenationParser(
            LiteralParser("A"), LiteralParser("B"), LiteralParser("C")
        ),
        SymbolsForTesting.A: LiteralParser("A"),
        SymbolsForTesting.B: LiteralParser("B"),
        SymbolsForTesting.C: LiteralParser("C"),
        SymbolsForTesting.D: LiteralParser("D"),
    }

    expected_ok = re.compile("ABC").fullmatch(code)

    try:
        new_parse_generic(
            rewrite_rules, SymbolsForTesting.PROGRAM, code, SymbolsForTesting
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    "code", ["A", "B", "C", "D", "AB", "AB ", "AC", "BC", "BD", "AA"]
)
def test_parser_optionals_with_concatenation(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        SymbolsForTesting.PROGRAM: ConcatenationParser(
            OrParser(
                SymbolParser(SymbolsForTesting.A), SymbolParser(SymbolsForTesting.B)
            ),
            OrParser(
                SymbolParser(SymbolsForTesting.C), SymbolParser(SymbolsForTesting.D)
            ),
        ),
        SymbolsForTesting.A: LiteralParser("A"),
        SymbolsForTesting.B: LiteralParser("B"),
        SymbolsForTesting.C: LiteralParser("C"),
        SymbolsForTesting.D: LiteralParser("D"),
    }

    expected_ok = re.compile("(A|B)(C|D)").fullmatch(code)

    try:
        new_parse_generic(
            rewrite_rules, SymbolsForTesting.PROGRAM, code, SymbolsForTesting
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize(
    "code", ["", "foo", "foobar", "foobarbaz", "-foobarbaz", "foobarbazquux"]
)
def test_parser_concatenate_three_symbols(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        SymbolsForTesting.PROGRAM: ConcatenationParser(
            SymbolParser(SymbolsForTesting.A),
            SymbolParser(SymbolsForTesting.B),
            SymbolParser(SymbolsForTesting.C),
        ),
        SymbolsForTesting.A: LiteralParser("foo"),
        SymbolsForTesting.B: LiteralParser("bar"),
        SymbolsForTesting.C: LiteralParser("baz"),
        SymbolsForTesting.D: LiteralParser("D"),
    }

    expected_ok = re.compile("foobarbaz").fullmatch(code)

    try:
        new_parse_generic(
            rewrite_rules, SymbolsForTesting.PROGRAM, code, SymbolsForTesting
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize("code", ["", "A", "B", "AB", "AAB", "AAAB", "BB", "ABB"])
def test_parser_repeat_symbols(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        SymbolsForTesting.PROGRAM: ConcatenationParser(
            RepeatParser(SymbolParser(SymbolsForTesting.A)),
            SymbolParser(SymbolsForTesting.B),
        ),
        SymbolsForTesting.A: LiteralParser("A"),
        SymbolsForTesting.B: LiteralParser("B"),
        SymbolsForTesting.C: LiteralParser("C"),
        SymbolsForTesting.D: LiteralParser("D"),
    }

    expected_ok = re.compile("A*B").fullmatch(code)

    try:
        new_parse_generic(
            rewrite_rules, SymbolsForTesting.PROGRAM, code, SymbolsForTesting
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize("code", ["", "A", "B", "AB", "AAB", "AAAB", "BB", "ABB"])
def test_parser_repeat_symbols_with_at_least_one(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        SymbolsForTesting.PROGRAM: ConcatenationParser(
            RepeatParser(SymbolParser(SymbolsForTesting.A), min_repeats=1),
            SymbolParser(SymbolsForTesting.B),
        ),
        SymbolsForTesting.A: LiteralParser("A"),
        SymbolsForTesting.B: LiteralParser("B"),
        SymbolsForTesting.C: LiteralParser("C"),
        SymbolsForTesting.D: LiteralParser("D"),
    }

    expected_ok = re.compile("A+B").fullmatch(code)

    try:
        new_parse_generic(
            rewrite_rules, SymbolsForTesting.PROGRAM, code, SymbolsForTesting
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


@pytest.mark.parametrize("code", ["", "AC", "ABC", "ABB", "CCB", "AAA"])
def test_parser_optional_symbol(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        SymbolsForTesting.PROGRAM: ConcatenationParser(
            SymbolParser(SymbolsForTesting.A),
            OptionalParser(SymbolParser(SymbolsForTesting.B)),
            SymbolParser(SymbolsForTesting.C),
        ),
        SymbolsForTesting.A: LiteralParser("A"),
        SymbolsForTesting.B: LiteralParser("B"),
        SymbolsForTesting.C: LiteralParser("C"),
        SymbolsForTesting.D: LiteralParser("D"),
    }

    expected_ok = re.compile("AB?C").fullmatch(code)

    try:
        new_parse_generic(
            rewrite_rules, SymbolsForTesting.PROGRAM, code, SymbolsForTesting
        )
    except ParseError:
        assert not expected_ok
    else:
        assert expected_ok


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

import re
from enum import IntEnum, auto
from typing import Dict

import pytest

from lang.tokenizer.generic import Parser, cat, lit, new_tokenize_generic, opt, rep, sym


class TestSymbolType(IntEnum):
    PROGRAM = auto()
    A = auto()
    B = auto()
    C = auto()
    D = auto()


# shorthand to keep tests readable
T = TestSymbolType


@pytest.mark.parametrize("code", ["", "A", "B", "C", "D", "AA", "DA", "AD"])
def test_new_tokenizer_three_options(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: sym(T.A) | sym(T.B) | sym(T.C),
        TestSymbolType.A: lit("A"),
        TestSymbolType.B: lit("B"),
        TestSymbolType.C: lit("C"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("A|B|C").fullmatch(code)
    result = new_tokenize_generic(
        rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType
    )
    assert bool(result) == bool(expected_ok)


@pytest.mark.parametrize("code", ["", "A", "foo", "f", "B", " foo", "foo ", " foo "])
def test_new_tokenizer_option_of_literal_and_symbol(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: (sym(T.A) | lit("foo")),
        TestSymbolType.A: lit("A"),
        TestSymbolType.B: lit("B"),
        TestSymbolType.C: lit("C"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("A|foo").fullmatch(code)
    result = new_tokenize_generic(
        rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType
    )
    assert bool(result) == bool(expected_ok)


@pytest.mark.parametrize("code", ["", "A", "AB", "ABC", " ABC", "ABC "])
def test_new_tokenizer_three_literals(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: cat(lit("A"), lit("B"), lit("C")),
        TestSymbolType.A: lit("A"),
        TestSymbolType.B: lit("B"),
        TestSymbolType.C: lit("C"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("ABC").fullmatch(code)
    result = new_tokenize_generic(
        rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType
    )
    assert bool(result) == bool(expected_ok)


@pytest.mark.parametrize(
    "code", ["A", "B", "C", "D", "AB", "AB ", "AC", "BC", "BD", "AA"]
)
def test_new_tokenizer_optionals_with_concatenation(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: cat((sym(T.A) | sym(T.B)), (sym(T.C) | sym(T.D))),
        TestSymbolType.A: lit("A"),
        TestSymbolType.B: lit("B"),
        TestSymbolType.C: lit("C"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("(A|B)(C|D)").fullmatch(code)
    result = new_tokenize_generic(
        rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType
    )
    assert bool(result) == bool(expected_ok)


@pytest.mark.parametrize(
    "code", ["", "foo", "foobar", "foobarbaz", "-foobarbaz", "foobarbazquux"]
)
def test_new_tokenizer_concatenate_three_symbols(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: cat(sym(T.A), sym(T.B), sym(T.C)),
        TestSymbolType.A: lit("foo"),
        TestSymbolType.B: lit("bar"),
        TestSymbolType.C: lit("baz"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("foobarbaz").fullmatch(code)
    result = new_tokenize_generic(
        rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType
    )
    assert bool(result) == bool(expected_ok)


@pytest.mark.parametrize("code", ["", "A", "B", "AB", "AAB", "AAAB", "BB", "ABB"])
def test_new_tokenizer_repeat_symbols(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: cat(rep(sym(T.A)), sym(T.B)),
        TestSymbolType.A: lit("A"),
        TestSymbolType.B: lit("B"),
        TestSymbolType.C: lit("C"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("A*B").fullmatch(code)
    result = new_tokenize_generic(
        rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType
    )
    assert bool(result) == bool(expected_ok)


@pytest.mark.parametrize("code", ["", "A", "B", "AB", "AAB", "AAAB", "BB", "ABB"])
def test_new_tokenizer_repeat_symbols_with_at_least_one(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: cat(rep(sym(T.A), m=1), sym(T.B)),
        TestSymbolType.A: lit("A"),
        TestSymbolType.B: lit("B"),
        TestSymbolType.C: lit("C"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("A+B").fullmatch(code)
    result = new_tokenize_generic(
        rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType
    )
    assert bool(result) == bool(expected_ok)


@pytest.mark.parametrize("code", ["", "AC", "ABC", "ABB", "CCB", "AAA"])
def test_new_tokenizer_optional_symbol(code: str) -> None:
    rewrite_rules: Dict[IntEnum, Parser] = {
        TestSymbolType.PROGRAM: cat(sym(T.A), opt(sym(T.B)), sym(T.C)),
        TestSymbolType.A: lit("A"),
        TestSymbolType.B: lit("B"),
        TestSymbolType.C: lit("C"),
        TestSymbolType.D: lit("D"),
    }

    expected_ok = re.compile("AB?C").fullmatch(code)
    result = new_tokenize_generic(
        rewrite_rules, TestSymbolType.PROGRAM, code, TestSymbolType
    )
    assert bool(result) == bool(expected_ok)


def test_flat_concatenation_expression() -> None:
    expr = cat(sym(T.A), sym(T.B), sym(T.C))
    assert len(expr.children) == 3


def test_flat_option_expression() -> None:
    expr = sym(T.A) | sym(T.B) | sym(T.C)
    assert len(expr.children) == 3

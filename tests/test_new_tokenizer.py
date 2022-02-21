import re
from typing import Dict

import pytest

from lang.new_tokenizer import (
    Parser,
    SymbolType,
    cat,
    eof,
    lit,
    new_parse_generic,
    opt,
    rep,
    sym,
)


@pytest.mark.parametrize("code", ["", "A", "B", "C", "D", "AA", "DA", "AD"])
def test_new_tokenizer_three_options(code: str) -> None:
    rewrite_rules = {
        SymbolType.PROGRAM: cat((sym("A") | sym("B") | sym("C")), eof()),
        SymbolType.A: lit("A"),
        SymbolType.B: lit("B"),
        SymbolType.C: lit("C"),
    }

    expected_ok = re.compile("A|B|C").fullmatch(code)
    result = new_parse_generic(rewrite_rules, SymbolType.PROGRAM, code)
    assert bool(result) == bool(expected_ok)


@pytest.mark.parametrize("code", ["", "A", "foo", "f", "B", " foo", "foo ", " foo "])
def test_new_tokenizer_option_of_literal_and_symbol(code: str) -> None:
    rewrite_rules = {
        SymbolType.PROGRAM: cat((sym("A") | lit("foo")), eof()),
        SymbolType.A: lit("A"),
    }

    expected_ok = re.compile("A|foo").fullmatch(code)
    result = new_parse_generic(rewrite_rules, SymbolType.PROGRAM, code)
    assert bool(result) == bool(expected_ok)


@pytest.mark.parametrize("code", ["", "A", "AB", "ABC", " ABC", "ABC "])
def test_new_tokenizer_three_literals(code: str) -> None:
    rewrite_rules: Dict[SymbolType, Parser] = {
        SymbolType.PROGRAM: cat(lit("A"), lit("B"), lit("C"), eof()),
    }

    expected_ok = re.compile("ABC").fullmatch(code)
    result = new_parse_generic(rewrite_rules, SymbolType.PROGRAM, code)
    assert bool(result) == bool(expected_ok)


@pytest.mark.parametrize(
    "code", ["A", "B", "C", "D", "AB", "AB ", "AC", "BC", "BD", "AA"]
)
def test_new_tokenizer_optionals_with_concatenation(code: str) -> None:
    rewrite_rules = {
        SymbolType.PROGRAM: cat((sym("A") | sym("B")), (sym("C") | sym("D")), eof()),
        SymbolType.A: lit("A"),
        SymbolType.B: lit("B"),
        SymbolType.C: lit("C"),
        SymbolType.D: lit("D"),
    }

    expected_ok = re.compile("(A|B)(C|D)").fullmatch(code)
    result = new_parse_generic(rewrite_rules, SymbolType.PROGRAM, code)
    assert bool(result) == bool(expected_ok)


@pytest.mark.parametrize(
    "code", ["", "foo", "foobar", "foobarbaz", "-foobarbaz", "foobarbazquux"]
)
def test_new_tokenizer_concatenate_three_symbols(code: str) -> None:
    rewrite_rules = {
        SymbolType.PROGRAM: cat(sym("A"), sym("B"), sym("C"), eof()),
        SymbolType.A: lit("foo"),
        SymbolType.B: lit("bar"),
        SymbolType.C: lit("baz"),
    }

    expected_ok = re.compile("foobarbaz").fullmatch(code)
    result = new_parse_generic(rewrite_rules, SymbolType.PROGRAM, code)
    assert bool(result) == bool(expected_ok)


@pytest.mark.parametrize("code", ["", "A", "B", "AB", "AAB", "AAAB", "BB", "ABB"])
def test_new_tokenizer_repeat_symbols(code: str) -> None:
    rewrite_rules = {
        SymbolType.PROGRAM: cat(rep(sym("A")), sym("B"), eof()),
        SymbolType.A: lit("A"),
        SymbolType.B: lit("B"),
    }

    expected_ok = re.compile("A*B").fullmatch(code)
    result = new_parse_generic(rewrite_rules, SymbolType.PROGRAM, code)
    assert bool(result) == bool(expected_ok)


@pytest.mark.parametrize("code", ["", "A", "B", "AB", "AAB", "AAAB", "BB", "ABB"])
def test_new_tokenizer_repeat_symbols_with_at_least_one(code: str) -> None:
    rewrite_rules = {
        SymbolType.PROGRAM: cat(rep(sym("A"), m=1), sym("B"), eof()),
        SymbolType.A: lit("A"),
        SymbolType.B: lit("B"),
    }

    expected_ok = re.compile("A+B").fullmatch(code)
    result = new_parse_generic(rewrite_rules, SymbolType.PROGRAM, code)
    assert bool(result) == bool(expected_ok)


@pytest.mark.parametrize("code", ["", "AC", "ABC", "ABB", "CCB", "AAA"])
def test_new_tokenizer_optional_symbol(code: str) -> None:
    rewrite_rules = {
        SymbolType.PROGRAM: cat(sym("A"), opt(sym("B")), sym("C"), eof()),
        SymbolType.A: lit("A"),
        SymbolType.B: lit("B"),
        SymbolType.C: lit("C"),
    }

    expected_ok = re.compile("AB?C").fullmatch(code)
    result = new_parse_generic(rewrite_rules, SymbolType.PROGRAM, code)
    assert bool(result) == bool(expected_ok)


def test_flat_concatenation_expression() -> None:
    expr = cat(sym("A"), sym("B"), sym("C"))
    assert len(expr.children) == 3


def test_flat_option_expression() -> None:
    expr = sym("A") | sym("B") | sym("C")
    assert len(expr.children) == 3

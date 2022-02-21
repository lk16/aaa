import re

import pytest

from lang.new_tokenizer import SymbolType, cat, eof, lit, new_parse_generic, sym


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


# TODO test A | "foo"

# TODO test A B C

# TODO test (A | B) (C | D)

# TODO test "foo" "bar" "baz"

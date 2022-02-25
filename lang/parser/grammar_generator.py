from enum import IntEnum
from pathlib import Path
from typing import Dict, Tuple

from lang.parser.generic import (
    ConcatenationParser,
    LiteralParser,
    OptionalParser,
    OrParser,
    Parser,
    RegexBasedParser,
    RepeatParser,
    SymbolParser,
)


def bnf_like_expression(parser: Parser) -> str:
    if parser.symbol_type is not None:
        return parser.symbol_type.name

    if isinstance(parser, SymbolParser):
        assert parser.symbol_type
        return parser.symbol_type.name

    elif isinstance(parser, ConcatenationParser):
        return " ".join(bnf_like_expression(child) for child in parser.children)

    elif isinstance(parser, OrParser):
        return (
            "("
            + " | ".join(bnf_like_expression(child) for child in parser.children)
            + ")"
        )

    elif isinstance(parser, OptionalParser):
        return "(" + bnf_like_expression(parser.child) + ")?"

    elif isinstance(parser, RepeatParser):
        expr = "(" + bnf_like_expression(parser.child) + ")"
        if parser.min_repeats == 0:
            return expr + "*"
        elif parser.min_repeats == 1:
            return expr + "+"
        else:
            return expr + f"{parser.min_repeats,...}"

    elif isinstance(parser, RegexBasedParser):
        return "regex(" + parser.regex.pattern[1:] + ")"

    elif isinstance(parser, LiteralParser):
        return f'"{parser.literal}"'

    else:  # pragma: nocover
        raise NotImplementedError


def check_grammar_file_staleness(
    grammar_file: Path, rewrite_rules: Dict[IntEnum, Parser]
) -> Tuple[bool, str]:
    if grammar_file.exists():
        old_grammar = grammar_file.read_text()
    else:
        old_grammar = ""

    new_grammar = regenerate_bnf_like_grammar_file(rewrite_rules)

    stale = old_grammar != new_grammar
    return stale, new_grammar


def regenerate_bnf_like_grammar_file(
    rewrite_rules: Dict[IntEnum, Parser],
) -> str:

    output = (
        "// Human readable grammar. Easier to understand than actual rewrite rules.\n"
        '// This file was generated using "./aaa.py generate-grammar-file".\n'
        "// A unit test should make sure this file is up to date with its source.\n\n"
    )

    symbols = sorted(rewrite_rules.keys(), key=lambda x: x.name)

    for i, symbol in enumerate(symbols):
        parser = rewrite_rules[symbol]
        output += f"{symbol.name} = " + bnf_like_expression(parser)

        if i == len(symbols) - 1:
            output += "\n"
        else:
            output += "\n\n"

    return output

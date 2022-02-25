#!/usr/bin/env python

import re
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type

from lang.exceptions import UnexpectedSymbols, UnhandledSymbolType
from lang.parser.exceptions import InternalParseError, ParseError
from lang.parser.tree import ParseTree


@dataclass
class Parser:
    symbol_type: Optional[IntEnum] = None

    def parse(self, code: str, offset: int) -> ParseTree:  # pragma: nocover
        raise NotImplementedError

    # TODO remove this
    def __or__(self, other: Any) -> "OrParser":
        if not isinstance(other, Parser):
            raise TypeError  # pragma: nocover

        return OrParser(self, other)


class OrParser(Parser):
    def __init__(self, *args: Parser) -> None:
        self.children = list(args)

    def parse(self, code: str, offset: int) -> ParseTree:
        longest_parsed: Optional[ParseTree] = None

        for child in self.children:
            try:
                parsed = child.parse(code, offset)
            except InternalParseError:
                continue

            if not longest_parsed:
                longest_parsed = parsed
            elif parsed.symbol_length > longest_parsed.symbol_length:
                longest_parsed = parsed

        if not longest_parsed:
            raise InternalParseError(offset, self.symbol_type)

        return longest_parsed

    # TODO remove this
    def __or__(self, other: Any) -> "OrParser":
        if not isinstance(other, Parser):
            raise TypeError  # pragma: nocover

        return OrParser(*self.children, other)


# TODO refactor such that regex doesn't start with '^'
class RegexBasedParser(Parser):
    def __init__(self, regex: str, forbidden: List[str] = []):
        self.regex = re.compile(regex)
        self.forbidden_matches = set(forbidden)

    def parse(self, code: str, offset: int) -> ParseTree:
        match = self.regex.match(code[offset:])

        if not match:
            raise InternalParseError(offset, self.symbol_type)

        if match.group(0) in self.forbidden_matches:
            raise InternalParseError(offset, self.symbol_type)

        return ParseTree(offset, len(match.group(0)), self.symbol_type, [])


class RepeatParser(Parser):
    def __init__(self, child: Parser, min_repeats: int = 0) -> None:
        self.child = child
        self.min_repeats = min_repeats

    def parse(self, code: str, offset: int) -> ParseTree:
        sub_trees: List[ParseTree] = []
        child_offset = offset

        while True:
            try:
                parsed = self.child.parse(code, child_offset)
            except InternalParseError:
                break
            else:
                sub_trees.append(parsed)
                child_offset += parsed.symbol_length

        if len(sub_trees) < self.min_repeats:
            raise InternalParseError(offset, self.child.symbol_type)

        return ParseTree(
            offset,
            child_offset - offset,
            self.symbol_type,
            sub_trees,
        )


class OptionalParser(Parser):
    def __init__(self, child: Parser) -> None:
        self.child = child

    def parse(self, code: str, offset: int) -> ParseTree:
        try:
            parsed = self.child.parse(code, offset)
        except InternalParseError:
            return ParseTree(
                offset,
                0,
                self.symbol_type,
                [],
            )
        else:
            return parsed


class ConcatenationParser(Parser):
    def __init__(self, *args: Parser) -> None:
        self.children = list(args)

    def parse(self, code: str, offset: int) -> ParseTree:
        sub_trees: List[ParseTree] = []

        child_offset = offset

        for child in self.children:
            parsed = child.parse(code, child_offset)
            sub_trees.append(parsed)
            child_offset += parsed.symbol_length

        return ParseTree(
            offset,
            child_offset - offset,
            self.symbol_type,
            sub_trees,
        )


class SymbolParser(Parser):
    def __init__(self, symbol_type: IntEnum):
        self.symbol_type = symbol_type
        self.rewrite_rules: Optional[Dict[IntEnum, Parser]] = None

    def parse(self, code: str, offset: int) -> ParseTree:
        assert self.symbol_type
        assert self.rewrite_rules

        rewritten_expression = self.rewrite_rules[self.symbol_type]
        rewritten_expression.symbol_type = self.symbol_type
        return rewritten_expression.parse(code, offset)


class LiteralParser(Parser):
    def __init__(self, literal: str):
        self.literal = literal

    def parse(self, code: str, offset: int) -> ParseTree:
        if not code[offset:].startswith(self.literal):
            raise InternalParseError(offset, self.symbol_type)

        return ParseTree(0, len(self.literal), self.symbol_type, [])


def set_rewrite_rules(parser: Parser, rewrite_rules: Dict[IntEnum, Parser]) -> None:
    if isinstance(parser, SymbolParser):
        parser.rewrite_rules = rewrite_rules

    elif isinstance(parser, (ConcatenationParser, OrParser)):
        for child in parser.children:
            set_rewrite_rules(child, rewrite_rules)

    elif isinstance(parser, (OptionalParser, RepeatParser)):
        set_rewrite_rules(parser.child, rewrite_rules)

    elif isinstance(parser, (RegexBasedParser, LiteralParser)):
        pass

    else:  # pragma: nocover
        raise NotImplementedError


def humanize_parse_error(code: str, e: InternalParseError) -> ParseError:
    before_offset = code[e.offset :]
    line_number = 1 + before_offset.count("\n")

    if line_number == 1:
        column_number = e.offset
        line = before_offset
    else:
        prev_newline = before_offset.rfind("\n")
        column_number = e.offset - prev_newline
        line = code[prev_newline + 1 : e.offset]

    # TODO use e.symbol_type to set this value
    expected_symbol_types: List[IntEnum] = []

    return ParseError(line_number, column_number, line, expected_symbol_types)


def new_parse_generic(
    rewrite_rules: Dict[IntEnum, Parser],
    root_symbol: IntEnum,
    code: str,
    symbols_enum: Type[IntEnum],
) -> ParseTree:

    for enum_value in symbols_enum:
        try:
            rewrite_rules[enum_value]
        except KeyError:
            raise UnhandledSymbolType(enum_value)

    if len(rewrite_rules) != len(symbols_enum):
        unexpected_keys = set(rewrite_rules.keys()) - set(symbols_enum)
        raise UnexpectedSymbols(unexpected_keys)

    for parser in rewrite_rules.values():
        set_rewrite_rules(parser, rewrite_rules)

    tree = rewrite_rules[root_symbol]
    tree.symbol_type = root_symbol

    try:
        parsed = tree.parse(code, 0)

        if parsed.symbol_length != len(code):
            raise InternalParseError(len(code), None)

    except InternalParseError as e:
        raise humanize_parse_error(code, e) from e

    return parsed


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
        return "regex(" + parser.regex.pattern + ")"

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

    stale = old_grammar == new_grammar
    return stale, new_grammar


def regenerate_bnf_like_grammar_file(
    rewrite_rules: Dict[IntEnum, Parser],
) -> str:

    output = (
        '// This file was generated using "./aaa.py generate-grammar-file"\n'
        "// A unit test should make sure this file is up to date with its source\n\n"
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

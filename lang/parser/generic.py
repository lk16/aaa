#!/usr/bin/env python

import re
from dataclasses import dataclass, replace
from enum import IntEnum
from typing import Dict, List, Optional, Type

from lang.exceptions import UnexpectedSymbols, UnhandledSymbolType
from lang.parser.exceptions import InternalParseError, ParseError
from lang.parser.symbol_tree import SymbolTree


@dataclass
class Parser:
    symbol_type: Optional[IntEnum] = None

    def parse(self, code: str, offset: int) -> SymbolTree:  # pragma: nocover
        raise NotImplementedError


class OrParser(Parser):
    def __init__(self, *args: Parser) -> None:
        self.children = list(args)

    def parse(self, code: str, offset: int) -> SymbolTree:
        longest_parsed: Optional[SymbolTree] = None

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


class RegexBasedParser(Parser):
    def __init__(self, regex: str, forbidden: List[str] = []):
        assert regex.startswith("^")
        self.regex = re.compile(regex)
        self.forbidden_matches = set(forbidden)

    def parse(self, code: str, offset: int) -> SymbolTree:
        match = self.regex.match(code[offset:])

        if not match:
            raise InternalParseError(offset, self.symbol_type)

        if match.group(0) in self.forbidden_matches:
            raise InternalParseError(offset, self.symbol_type)

        return SymbolTree(offset, len(match.group(0)), self.symbol_type, [])


class RepeatParser(Parser):
    def __init__(self, child: Parser, min_repeats: int = 0) -> None:
        self.child = child
        self.min_repeats = min_repeats

    def parse(self, code: str, offset: int) -> SymbolTree:
        sub_trees: List[SymbolTree] = []
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

        return SymbolTree(
            offset,
            child_offset - offset,
            self.symbol_type,
            sub_trees,
        )


class OptionalParser(Parser):
    def __init__(self, child: Parser) -> None:
        self.child = child

    def parse(self, code: str, offset: int) -> SymbolTree:
        try:
            parsed = self.child.parse(code, offset)
        except InternalParseError:
            return SymbolTree(
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

    def parse(self, code: str, offset: int) -> SymbolTree:
        sub_trees: List[SymbolTree] = []

        child_offset = offset

        for child in self.children:
            parsed = child.parse(code, child_offset)
            sub_trees.append(parsed)
            child_offset += parsed.symbol_length

        return SymbolTree(
            offset,
            child_offset - offset,
            self.symbol_type,
            sub_trees,
        )


class SymbolParser(Parser):
    def __init__(self, symbol_type: IntEnum):
        self.symbol_type = symbol_type
        self.rewrite_rules: Optional[Dict[IntEnum, Parser]] = None

    def parse(self, code: str, offset: int) -> SymbolTree:

        assert self.symbol_type
        assert self.rewrite_rules

        rewritten_expression = self.rewrite_rules[self.symbol_type]
        rewritten_expression.symbol_type = self.symbol_type
        tree = rewritten_expression.parse(code, offset)

        if tree.symbol_type is None:
            tree = replace(tree, symbol_type=self.symbol_type)

        return tree


class LiteralParser(Parser):
    def __init__(self, literal: str):
        self.literal = literal

    def parse(self, code: str, offset: int) -> SymbolTree:
        if not code[offset:].startswith(self.literal):
            raise InternalParseError(offset, self.symbol_type)

        return SymbolTree(offset, len(self.literal), self.symbol_type, [])


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
    before_offset = code[: e.offset]
    line_number = 1 + before_offset.count("\n")
    prev_newline = before_offset.rfind("\n")

    next_newline = code.find("\n", e.offset)
    if next_newline == -1:
        next_newline = len(code)

    column_number = e.offset - prev_newline
    line = code[prev_newline + 1 : next_newline]

    expected_symbol_types: List[IntEnum] = []

    if e.symbol_type:
        # TODO this may be wrong or unhelpful to the programmer
        expected_symbol_types.append(e.symbol_type)

    return ParseError(line_number, column_number, line, expected_symbol_types)


def new_parse_generic(
    rewrite_rules: Dict[IntEnum, Parser],
    root_symbol: IntEnum,
    code: str,
    symbols_enum: Type[IntEnum],
) -> SymbolTree:

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

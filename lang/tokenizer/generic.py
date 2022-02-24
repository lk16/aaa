#!/usr/bin/env python

import re
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, List, Optional, Type

from lang.exceptions import UnexpectedSymbols, UnhandledSymbolType


@dataclass
class ParseTree:
    symbol_offset: int
    symbol_length: int
    symbol_type: Optional[IntEnum]
    children: List["ParseTree"]


@dataclass
class Parser:
    symbol_type: Optional[IntEnum] = None

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:  # pragma: nocover
        raise NotImplementedError

    def set_rewrite_rules(self, rewrite_rules: Dict[IntEnum, "Parser"]) -> None:
        # This facilitates testing
        pass

    def __or__(self, other: Any) -> "OrParser":
        if not isinstance(other, Parser):
            raise TypeError  # pragma: nocover

        return OrParser(self, other)


class OrParser(Parser):
    def __init__(self, *args: "Parser") -> None:
        self.children = list(args)

    def set_rewrite_rules(self, rewrite_rules: Dict[IntEnum, "Parser"]) -> None:
        for child in self.children:
            child.set_rewrite_rules(rewrite_rules)

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        longest_parsed: Optional[ParseTree] = None

        for child in self.children:
            parsed = child.parse(code, offset)
            if parsed:
                if (
                    not longest_parsed
                ) or parsed.symbol_length > longest_parsed.symbol_length:
                    longest_parsed = parsed

        return longest_parsed

    def __or__(self, other: Any) -> "OrParser":
        if not isinstance(other, Parser):
            raise TypeError  # pragma: nocover

        return OrParser(*self.children, other)


class RegexBasedParser(Parser):
    def __init__(self, regex: str):
        self.regex = re.compile(regex)

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        match = self.regex.match(code)

        if not match:
            return None

        return ParseTree(offset, len(match.group(0)), self.symbol_type, [])


class RepeatParser(Parser):
    def __init__(self, child: Parser, min_repeats: int = 0) -> None:
        self.child = child
        self.min_repeats = min_repeats

    def set_rewrite_rules(self, rewrite_rules: Dict[IntEnum, "Parser"]) -> None:
        self.child.set_rewrite_rules(rewrite_rules)

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        sub_trees: List[ParseTree] = []
        child_offset = offset

        while True:
            parsed = self.child.parse(code, child_offset)
            if parsed:
                sub_trees.append(parsed)
                child_offset += parsed.symbol_length
            else:
                break

        if len(sub_trees) < self.min_repeats:
            return None

        return ParseTree(
            offset,
            child_offset - offset,
            self.symbol_type,
            sub_trees,
        )


class OpionalParser(Parser):
    def __init__(self, child: Parser) -> None:
        self.child = child

    def set_rewrite_rules(self, rewrite_rules: Dict[IntEnum, "Parser"]) -> None:
        self.child.set_rewrite_rules(rewrite_rules)

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        parsed = self.child.parse(code, offset)
        if parsed:
            return parsed

        return ParseTree(
            offset,
            0,
            self.symbol_type,
            [],
        )


class ConcatenationParser(Parser):
    def __init__(self, *args: "Parser") -> None:
        self.children = list(args)

    def set_rewrite_rules(self, rewrite_rules: Dict[IntEnum, "Parser"]) -> None:
        for child in self.children:
            child.set_rewrite_rules(rewrite_rules)

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        sub_trees: List[ParseTree] = []

        child_offset = offset

        for child in self.children:
            parsed = child.parse(code, child_offset)
            if parsed:
                sub_trees.append(parsed)
                child_offset += parsed.symbol_length
            else:
                return None

        return ParseTree(
            offset,
            child_offset - offset,
            self.symbol_type,
            sub_trees,
        )


class SymbolParser(Parser):
    def __init__(self, symbol_type: IntEnum):
        self.symbol_type = symbol_type
        self.rewrite_rules: Optional[Dict[IntEnum, "Parser"]] = None

    def set_rewrite_rules(self, rewrite_rules: Dict[IntEnum, "Parser"]) -> None:
        self.rewrite_rules = rewrite_rules

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        assert self.symbol_type
        assert self.rewrite_rules

        rewritten_expression = self.rewrite_rules[self.symbol_type]
        rewritten_expression.symbol_type = self.symbol_type
        return rewritten_expression.parse(code, offset)


class LiteralParser(Parser):
    def __init__(self, literal: str):
        self.literal = literal

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        if code[offset:].startswith(self.literal):
            return ParseTree(0, len(self.literal), self.symbol_type, [])
        return None


def cat(*args: Parser) -> ConcatenationParser:
    return ConcatenationParser(*args)


def sym(symbol_type: IntEnum) -> SymbolParser:
    # TODO consider using partial
    return SymbolParser(symbol_type)


def lit(literal: str) -> LiteralParser:
    return LiteralParser(literal)


def rep(parser: Parser, m: int = 0) -> RepeatParser:
    return RepeatParser(parser, m)


def opt(parser: Parser) -> OpionalParser:
    return OpionalParser(parser)


def new_tokenize_generic(
    rewrite_rules: Dict[IntEnum, Parser],
    root_symbol: IntEnum,
    code: str,
    symbols_enum: Type[IntEnum],
) -> Optional[ParseTree]:

    for enum_value in symbols_enum:
        try:
            rewrite_rules[enum_value]
        except KeyError:
            raise UnhandledSymbolType(enum_value)

    if len(rewrite_rules) != len(symbols_enum):
        unexpected_keys = set(rewrite_rules.keys()) - set(symbols_enum)
        raise UnexpectedSymbols(unexpected_keys)

    for parser in rewrite_rules.values():
        parser.set_rewrite_rules(rewrite_rules)

    tree = rewrite_rules[root_symbol]
    tree.symbol_type = root_symbol
    parsed = tree.parse(code, 0)

    if parsed is not None and parsed.symbol_length == len(code):
        return parsed

    return None

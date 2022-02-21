#!/usr/bin/env python

from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Any, Dict, List, Optional


class SymbolType(IntEnum):
    PROGRAM = auto()
    A = auto()
    B = auto()
    C = auto()
    D = auto()
    END_OF_FILE = auto()


@dataclass
class ParseTree:
    symbol_offset: int
    symbol_length: int
    symbol_type: Optional[SymbolType]
    children: List["ParseTree"]


@dataclass
class Parser:
    symbol_type: Optional[SymbolType] = None

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        raise NotImplementedError

    def set_rewrite_rules(self, rewrite_rules: Dict[SymbolType, "Parser"]) -> None:
        # This facilitates testing
        pass

    def __or__(self, other: Any) -> "OrExpression":
        if not isinstance(other, Parser):
            raise TypeError

        return OrExpression(self, other)


REWRITE_RULES: Dict[SymbolType, Parser]


class EndOfFileExpression(Parser):
    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        if len(code) != offset:
            return None

        return ParseTree(offset, 0, self.symbol_type, [])


class OrExpression(Parser):
    def __init__(self, *args: "Parser") -> None:
        self.options = list(args)

    def set_rewrite_rules(self, rewrite_rules: Dict[SymbolType, "Parser"]) -> None:
        for option in self.options:
            option.set_rewrite_rules(rewrite_rules)

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        for option in self.options:
            parsed = option.parse(code, offset)
            if parsed:
                return parsed
        return None


class ConcatenationExpression(Parser):
    def __init__(self, *args: "Parser") -> None:
        self.values = list(args)

    def set_rewrite_rules(self, rewrite_rules: Dict[SymbolType, "Parser"]) -> None:
        for value in self.values:
            value.set_rewrite_rules(rewrite_rules)

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        sub_trees: List[ParseTree] = []

        for value in self.values:
            parsed = value.parse(code, offset)
            if parsed:
                sub_trees.append(parsed)
                offset += parsed.symbol_length
            else:
                return None

        return ParseTree(
            sub_trees[0].symbol_offset,
            sum(sub_tree.symbol_length for sub_tree in sub_trees),
            self.symbol_type,
            sub_trees,
        )


class SymbolExpression(Parser):
    def __init__(self, symbol_type: SymbolType):
        self.symbol_type = symbol_type
        self.rewrite_rules: Optional[Dict[SymbolType, "Parser"]] = None

    def set_rewrite_rules(self, rewrite_rules: Dict[SymbolType, "Parser"]) -> None:
        self.rewrite_rules = rewrite_rules

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        assert self.symbol_type  # nosec
        assert self.rewrite_rules  # no sec

        rewritten_expression = self.rewrite_rules[self.symbol_type]
        rewritten_expression.symbol_type = self.symbol_type
        return rewritten_expression.parse(code, offset)


class LiteralExpression(Parser):
    def __init__(self, literal: str):
        self.literal = literal

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        if code[offset:].startswith(self.literal):
            return ParseTree(0, len(self.literal), self.symbol_type, [])
        return None


def cat(*args: Parser) -> ConcatenationExpression:
    return ConcatenationExpression(*args)


def sym(symbol_name: str) -> SymbolExpression:
    return SymbolExpression(SymbolType[symbol_name])


def eof() -> EndOfFileExpression:
    return EndOfFileExpression(SymbolType.END_OF_FILE)


def lit(literal: str) -> LiteralExpression:
    return LiteralExpression(literal)


def new_parse_generic(
    rewrite_rules: Dict[SymbolType, Parser], root_symbol: SymbolType, code: str
) -> Optional[ParseTree]:
    tree = rewrite_rules[root_symbol]
    tree.set_rewrite_rules(rewrite_rules)
    tree.symbol_type = root_symbol
    return tree.parse(code, 0)


REWRITE_RULES = {
    SymbolType.PROGRAM: cat((sym("A") | sym("B")), eof()),
    SymbolType.A: LiteralExpression("A"),
    SymbolType.B: LiteralExpression("B"),
}

ROOT_SYMBOL = SymbolType.PROGRAM


def new_parse(code: str) -> Optional[ParseTree]:
    return new_parse_generic(REWRITE_RULES, ROOT_SYMBOL, code)

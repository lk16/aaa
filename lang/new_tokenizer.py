#!/usr/bin/env python

from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Any, Dict, List, Optional


class SymbolType(IntEnum):
    PROGRAM = auto()
    A = auto()
    B = auto()
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

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        for option in self.options:
            parsed = option.parse(code, offset)
            if parsed:
                return parsed
        return None


class ConcatenationExpression(Parser):
    def __init__(self, *args: "Parser") -> None:
        self.values = list(args)

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


def cat(*args: Parser) -> ConcatenationExpression:
    return ConcatenationExpression(*args)


class SymbolExpression(Parser):
    def __init__(self, symbol_type: SymbolType):
        self.symbol_type = symbol_type

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        assert self.symbol_type  # nosec
        rewritten_expression = REWRITE_RULES[self.symbol_type]
        rewritten_expression.symbol_type = self.symbol_type
        return rewritten_expression.parse(code, offset)


class LiteralExpression(Parser):
    def __init__(self, literal: str):
        self.literal = literal

    def parse(self, code: str, offset: int) -> Optional[ParseTree]:
        if code[offset:].startswith(self.literal):
            return ParseTree(0, len(self.literal), self.symbol_type, [])
        return None


def sym(symbol_name: str) -> SymbolExpression:
    return SymbolExpression(SymbolType[symbol_name])


def eof() -> EndOfFileExpression:
    return EndOfFileExpression(SymbolType.END_OF_FILE)


REWRITE_RULES = {
    SymbolType.PROGRAM: cat((sym("A") | sym("B")), eof()),
    SymbolType.A: LiteralExpression("A"),
    SymbolType.B: LiteralExpression("B"),
}


ROOT_SYMBOL = SymbolType.PROGRAM


def new_parse(code: str) -> Optional[ParseTree]:
    tree = REWRITE_RULES[ROOT_SYMBOL]
    tree.symbol_type = ROOT_SYMBOL
    return tree.parse(code, 0)

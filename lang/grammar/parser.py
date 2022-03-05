# ===================================== #
# THIS FILE WAS GENERATED, DO NOT EDIT! #
# ===================================== #

# flake8: noqa
# fmt: off

from enum import IntEnum, auto
from parser.parser import (
    ConcatenationParser,
    LiteralParser,
    OptionalParser,
    OrParser,
    Parser,
    RegexBasedParser,
    RepeatParser,
    SymbolParser,
    parse_generic,
)
from parser.tree import Tree, prune_by_symbol_types
from typing import Dict, Final, Optional, Set


class SymbolType(IntEnum):
    BOOLEAN_LITERAL = auto()
    BRANCH = auto()
    FUNCTION_BODY = auto()
    FUNCTION_BODY_ITEM = auto()
    FUNCTION_DEFINITION = auto()
    IDENTIFIER = auto()
    INTEGER_LITERAL = auto()
    LITERAL = auto()
    LOOP = auto()
    OPERATOR = auto()
    ROOT = auto()
    STRING_LITERAL = auto()
    WHITESPACE = auto()


REWRITE_RULES: Final[Dict[IntEnum, Parser]] = {
    SymbolType.BOOLEAN_LITERAL: OrParser(LiteralParser("true"), LiteralParser("false")),
    SymbolType.BRANCH: ConcatenationParser(
        LiteralParser("if"),
        OptionalParser(
            ConcatenationParser(
                SymbolParser(SymbolType.WHITESPACE),
                SymbolParser(SymbolType.FUNCTION_BODY),
            )
        ),
    ),
    SymbolType.FUNCTION_BODY: ConcatenationParser(
        SymbolParser(SymbolType.FUNCTION_BODY_ITEM),
        RepeatParser(
            ConcatenationParser(
                SymbolParser(SymbolType.WHITESPACE),
                SymbolParser(SymbolType.FUNCTION_BODY_ITEM),
            )
        ),
    ),
    SymbolType.FUNCTION_BODY_ITEM: OrParser(
        SymbolParser(SymbolType.BRANCH),
        SymbolParser(SymbolType.LOOP),
        SymbolParser(SymbolType.OPERATOR),
        SymbolParser(SymbolType.IDENTIFIER),
        SymbolParser(SymbolType.LITERAL),
    ),
    SymbolType.FUNCTION_DEFINITION: ConcatenationParser(
        LiteralParser("fn"),
        SymbolParser(SymbolType.WHITESPACE),
        RepeatParser(
            ConcatenationParser(
                SymbolParser(SymbolType.IDENTIFIER), SymbolParser(SymbolType.WHITESPACE)
            ),
            min_repeats=1,
        ),
    ),
    SymbolType.IDENTIFIER: RegexBasedParser(
        "[a-z_]+",
        forbidden=[
            "and",
            "drop",
            "dup",
            "else",
            "end",
            "false",
            "fn",
            "if",
            "not",
            "or",
            "over",
            "rot",
            "strlen",
            "true",
            "substr",
            "swap",
            "while",
        ],
    ),
    SymbolType.INTEGER_LITERAL: RegexBasedParser("[0-9]+", forbidden=[]),
    SymbolType.LITERAL: OrParser(
        SymbolParser(SymbolType.BOOLEAN_LITERAL),
        SymbolParser(SymbolType.INTEGER_LITERAL),
        SymbolParser(SymbolType.STRING_LITERAL),
    ),
    SymbolType.LOOP: ConcatenationParser(
        LiteralParser("while"),
        SymbolParser(SymbolType.WHITESPACE),
        OptionalParser(
            ConcatenationParser(
                SymbolParser(SymbolType.FUNCTION_BODY),
                SymbolParser(SymbolType.WHITESPACE),
            )
        ),
    ),
    SymbolType.OPERATOR: OrParser(
        LiteralParser("-"),
        LiteralParser("!="),
        LiteralParser("."),
        LiteralParser("*"),
        LiteralParser("/"),
        LiteralParser("\n"),
        LiteralParser("%"),
        LiteralParser("+"),
        LiteralParser("<"),
        LiteralParser("<="),
        LiteralParser("="),
        LiteralParser(">"),
        LiteralParser(">="),
        LiteralParser("and"),
        LiteralParser("drop"),
        LiteralParser("dup"),
        LiteralParser("not"),
        LiteralParser("or"),
        LiteralParser("over"),
        LiteralParser("rot"),
        LiteralParser("strlen"),
        LiteralParser("substr"),
        LiteralParser("swap"),
    ),
    SymbolType.ROOT: OptionalParser(SymbolParser(SymbolType.WHITESPACE)),
    SymbolType.STRING_LITERAL: RegexBasedParser('"([^\\]|\\("|n|\\))*?"', forbidden=[]),
    SymbolType.WHITESPACE: RegexBasedParser("([ \n]|$)+", forbidden=[]),
}


HARD_PRUNED_SYMBOL_TYPES: Set[IntEnum] = {
    SymbolType.WHITESPACE,
}


SOFT_PRUNED_SYMBOL_TYPES: Set[IntEnum] = {
    SymbolType.FUNCTION_BODY_ITEM,
    SymbolType.LITERAL,
}


def parse(code: str) -> Tree:
    tree: Optional[Tree] = parse_generic(REWRITE_RULES, code)

    tree = prune_by_symbol_types(tree, HARD_PRUNED_SYMBOL_TYPES, prune_subtree=True)
    assert tree

    tree = prune_by_symbol_types(tree, SOFT_PRUNED_SYMBOL_TYPES, prune_subtree=False)
    assert tree

    return tree

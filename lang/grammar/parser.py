# ===================================== #
# THIS FILE WAS GENERATED, DO NOT EDIT! #
# ===================================== #

# flake8: noqa
# fmt: off
# nopycln: file

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
    BEGIN = auto()
    BOOLEAN_LITERAL = auto()
    BRANCH = auto()
    CONTROL_FLOW_KEYWORD = auto()
    ELSE = auto()
    END = auto()
    FN = auto()
    FORBIDDEN_IDENTIFIER = auto()
    FUNCTION_BODY = auto()
    FUNCTION_BODY_ITEM = auto()
    FUNCTION_DEFINITION = auto()
    FUNCTION_NAME_AND_ARGS = auto()
    IDENTIFIER = auto()
    IF = auto()
    INTEGER_LITERAL = auto()
    LITERAL = auto()
    LOOP = auto()
    OPERATOR = auto()
    OPERATOR_KEYWORD = auto()
    OPERATOR_NON_ALPHABETICAL = auto()
    ROOT = auto()
    STRING_LITERAL = auto()
    WHILE = auto()
    WHITESPACE = auto()


REWRITE_RULES: Final[Dict[IntEnum, Parser]] = {
    SymbolType.BEGIN: LiteralParser("begin"),
    SymbolType.BOOLEAN_LITERAL: OrParser(LiteralParser("true"), LiteralParser("false")),
    SymbolType.BRANCH: ConcatenationParser(
        SymbolParser(SymbolType.IF),
        OptionalParser(
            ConcatenationParser(
                SymbolParser(SymbolType.WHITESPACE),
                SymbolParser(SymbolType.FUNCTION_BODY),
            )
        ),
        SymbolParser(SymbolType.WHITESPACE),
        OptionalParser(
            ConcatenationParser(
                SymbolParser(SymbolType.ELSE),
                OptionalParser(
                    ConcatenationParser(
                        SymbolParser(SymbolType.WHITESPACE),
                        SymbolParser(SymbolType.FUNCTION_BODY),
                    )
                ),
                SymbolParser(SymbolType.WHITESPACE),
            )
        ),
        SymbolParser(SymbolType.END),
    ),
    SymbolType.CONTROL_FLOW_KEYWORD: OrParser(
        SymbolParser(SymbolType.IF),
        SymbolParser(SymbolType.ELSE),
        SymbolParser(SymbolType.BEGIN),
        SymbolParser(SymbolType.END),
        SymbolParser(SymbolType.WHILE),
        SymbolParser(SymbolType.FN),
    ),
    SymbolType.ELSE: LiteralParser("else"),
    SymbolType.END: LiteralParser("end"),
    SymbolType.FN: LiteralParser("fn"),
    SymbolType.FORBIDDEN_IDENTIFIER: OrParser(
        SymbolParser(SymbolType.BOOLEAN_LITERAL),
        SymbolParser(SymbolType.CONTROL_FLOW_KEYWORD),
        SymbolParser(SymbolType.OPERATOR_KEYWORD),
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
        SymbolParser(SymbolType.FN),
        SymbolParser(SymbolType.WHITESPACE),
        SymbolParser(SymbolType.FUNCTION_NAME_AND_ARGS),
        SymbolParser(SymbolType.WHITESPACE),
        SymbolParser(SymbolType.BEGIN),
        SymbolParser(SymbolType.WHITESPACE),
        OptionalParser(
            ConcatenationParser(
                SymbolParser(SymbolType.FUNCTION_BODY),
                SymbolParser(SymbolType.WHITESPACE),
            )
        ),
        SymbolParser(SymbolType.END),
    ),
    SymbolType.FUNCTION_NAME_AND_ARGS: ConcatenationParser(
        SymbolParser(SymbolType.IDENTIFIER),
        RepeatParser(
            ConcatenationParser(
                SymbolParser(SymbolType.WHITESPACE), SymbolParser(SymbolType.IDENTIFIER)
            )
        ),
    ),
    SymbolType.IDENTIFIER: RegexBasedParser(
        "[a-z_]+", forbidden=SymbolParser(SymbolType.FORBIDDEN_IDENTIFIER)
    ),
    SymbolType.IF: LiteralParser("if"),
    SymbolType.INTEGER_LITERAL: RegexBasedParser("[0-9]+"),
    SymbolType.LITERAL: OrParser(
        SymbolParser(SymbolType.BOOLEAN_LITERAL),
        SymbolParser(SymbolType.INTEGER_LITERAL),
        SymbolParser(SymbolType.STRING_LITERAL),
    ),
    SymbolType.LOOP: ConcatenationParser(
        SymbolParser(SymbolType.WHILE),
        SymbolParser(SymbolType.WHITESPACE),
        OptionalParser(
            ConcatenationParser(
                SymbolParser(SymbolType.FUNCTION_BODY),
                SymbolParser(SymbolType.WHITESPACE),
            )
        ),
        SymbolParser(SymbolType.END),
    ),
    SymbolType.OPERATOR: OrParser(
        SymbolParser(SymbolType.OPERATOR_NON_ALPHABETICAL),
        SymbolParser(SymbolType.OPERATOR_KEYWORD),
    ),
    SymbolType.OPERATOR_KEYWORD: OrParser(
        LiteralParser("and"),
        LiteralParser("drop"),
        LiteralParser("dup"),
        LiteralParser("not"),
        LiteralParser("nop"),
        LiteralParser("or"),
        LiteralParser("over"),
        LiteralParser("rot"),
        LiteralParser("strlen"),
        LiteralParser("substr"),
        LiteralParser("swap"),
    ),
    SymbolType.OPERATOR_NON_ALPHABETICAL: OrParser(
        LiteralParser("-"),
        LiteralParser("!="),
        LiteralParser("."),
        LiteralParser("*"),
        LiteralParser("/"),
        LiteralParser("\\n"),
        LiteralParser("%"),
        LiteralParser("+"),
        LiteralParser("<"),
        LiteralParser("<="),
        LiteralParser("="),
        LiteralParser(">"),
        LiteralParser(">="),
    ),
    SymbolType.ROOT: ConcatenationParser(
        OptionalParser(SymbolParser(SymbolType.WHITESPACE)),
        RepeatParser(
            ConcatenationParser(
                SymbolParser(SymbolType.FUNCTION_DEFINITION),
                SymbolParser(SymbolType.WHITESPACE),
            ),
            min_repeats=1,
        ),
        OptionalParser(SymbolParser(SymbolType.WHITESPACE)),
    ),
    SymbolType.STRING_LITERAL: RegexBasedParser('"([^\\\\]|\\\\("|n|\\\\))*?"'),
    SymbolType.WHILE: LiteralParser("while"),
    SymbolType.WHITESPACE: RegexBasedParser("([ \n]|$)+"),
}


HARD_PRUNED_SYMBOL_TYPES: Set[IntEnum] = {
    SymbolType.WHITESPACE,
}


SOFT_PRUNED_SYMBOL_TYPES: Set[IntEnum] = {
    SymbolType.CONTROL_FLOW_KEYWORD,
    SymbolType.FUNCTION_BODY_ITEM,
    SymbolType.LITERAL,
    SymbolType.OPERATOR,
}


def parse(code: str) -> Tree:
    return parse_generic(
        REWRITE_RULES, code, HARD_PRUNED_SYMBOL_TYPES, SOFT_PRUNED_SYMBOL_TYPES
    )

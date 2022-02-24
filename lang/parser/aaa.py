from enum import IntEnum, auto
from typing import Dict, Optional

from lang.parser.generic import (
    OrParser,
    Parser,
    ParseTree,
    RegexBasedParser,
    cat,
    lit,
    new_parse_generic,
    opt,
    rep,
    sym,
)


class SymbolType(IntEnum):
    FUNCTION_BODY = auto()
    WHITESPACE = auto()
    OPERATION = auto()
    IDENTIFIER = auto()
    LITERAL = auto()
    LOOP = auto()
    BRANCH = auto()
    STRING_LITERAL = auto()
    INTEGER_LITERAL = auto()
    BOOLEAN_LITERAL = auto()
    FUNCTION_DEFINITION = auto()
    FILE = auto()


OPERATION_LITERALS = [
    "-",
    "!=",
    ".",
    "*",
    "/",
    "\\n",
    "%",
    "+",
    "<",
    "<=",
    "=",
    ">",
    ">=",
    "and",
    "drop",
    "dup",
    "not",
    "or",
    "over",
    "rot",
    "strlen",
    "substr",
    "swap",
]

RESERVED_KEYWORDS = [
    "begin",
    "else",
    "end",
    "false",
    "fn",
    "if",
    "true",
    "while",
]

FORBIDDEN_IDENTIFIERS = RESERVED_KEYWORDS + OPERATION_LITERALS


# Shorthand to keep REWRITE_RULES readable
S = SymbolType

REWRITE_RULES: Dict[IntEnum, Parser] = {
    S.BOOLEAN_LITERAL: lit("true") | lit("false"),
    S.INTEGER_LITERAL: RegexBasedParser("^[0-9]+"),
    S.STRING_LITERAL: RegexBasedParser('^"([^\\\\]|\\\\("|n|\\\\))*"'),
    S.IDENTIFIER: RegexBasedParser("^[a-z_]+", forbidden=FORBIDDEN_IDENTIFIERS),
    S.LITERAL: sym(S.BOOLEAN_LITERAL) | sym(S.INTEGER_LITERAL) | sym(S.STRING_LITERAL),
    S.OPERATION: OrParser(*[lit(op) for op in OPERATION_LITERALS]),
    S.WHITESPACE: RegexBasedParser("^[ \\n]+"),
    S.BRANCH: cat(
        lit("if"),
        opt(
            cat(
                sym(S.WHITESPACE),
                sym(S.FUNCTION_BODY),
            )
        ),
        sym(S.WHITESPACE),
        opt(
            cat(
                lit("else"),
                opt(cat(sym(S.WHITESPACE), sym(S.FUNCTION_BODY))),
                sym(S.WHITESPACE),
            )
        ),
        lit("end"),
    ),
    S.LOOP: cat(
        lit("while"),
        sym(S.WHITESPACE),
        opt(cat(sym(S.FUNCTION_BODY), sym(S.WHITESPACE))),
        lit("end"),
    ),
    S.FUNCTION_BODY: cat(
        cat(
            sym(S.BRANCH)
            | sym(S.LOOP)
            | sym(S.OPERATION)
            | sym(S.IDENTIFIER)
            | sym(S.LITERAL),
        ),
        rep(
            cat(
                sym(S.WHITESPACE),
                sym(S.BRANCH)
                | sym(S.LOOP)
                | sym(S.OPERATION)
                | sym(S.IDENTIFIER)
                | sym(S.LITERAL),
            ),
        ),
    ),
    S.FUNCTION_DEFINITION: cat(
        lit("fn"),
        sym(S.WHITESPACE),
        sym(S.IDENTIFIER),
        sym(S.WHITESPACE),
        rep(cat(sym(S.IDENTIFIER), sym(S.WHITESPACE))),
        lit("begin"),
        sym(S.WHITESPACE),
        opt(cat(sym(S.FUNCTION_BODY), sym(S.WHITESPACE))),
        lit("end"),
    ),
    S.FILE: cat(
        opt(sym(S.WHITESPACE)),
        sym(S.FUNCTION_DEFINITION),
        rep(cat(sym(S.WHITESPACE), sym(S.FUNCTION_DEFINITION))),
        opt(sym(S.WHITESPACE)),
    ),
}

ROOT_SYMBOL = S.BRANCH


def new_parse(code: str) -> Optional[ParseTree]:  # pragma: nocover
    # NOTE Tests call new_tokenize_generic() directly
    return new_parse_generic(REWRITE_RULES, ROOT_SYMBOL, code, SymbolType)

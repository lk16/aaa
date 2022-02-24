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
        sym(S.FUNCTION_BODY),
        opt(cat(lit("else"), sym(S.FUNCTION_BODY))),
        lit("end"),
    ),
    S.LOOP: cat(lit("while"), sym(S.FUNCTION_BODY), lit("end")),
    S.FUNCTION_BODY: cat(
        sym(S.WHITESPACE),
        rep(
            cat(
                sym(S.BRANCH)
                | sym(S.LOOP)
                | sym(S.OPERATION)
                | sym(S.IDENTIFIER)
                | sym(S.LITERAL),
                sym(S.WHITESPACE),
            ),
        ),
    ),
}

ROOT_SYMBOL = S.FUNCTION_BODY


def new_parse(code: str) -> Optional[ParseTree]:  # pragma: nocover
    # NOTE Tests call new_tokenize_generic() directly
    return new_parse_generic(REWRITE_RULES, ROOT_SYMBOL, code, SymbolType)

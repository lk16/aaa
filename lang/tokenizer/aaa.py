from enum import IntEnum, auto
from typing import Dict, Optional

from lang.tokenizer.generic import (
    Parser,
    ParseTree,
    RegexBasedParser,
    cat,
    lit,
    new_tokenize_generic,
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
    IF = auto()
    ELSE = auto()
    END = auto()
    WHILE = auto()
    STRING_LITERAL = auto()
    INTEGER_LITERAL = auto()
    BOOLEAN_LITERAL = auto()
    DOUBLE_QUOTE = auto()
    WHITESPACE_CHAR = auto()
    NEWLINE = auto()
    SPACE = auto()


# Shorthand to keep REWRITE_RULES readable
S = SymbolType

REWRITE_RULES: Dict[IntEnum, Parser] = {
    S.FUNCTION_BODY: cat(
        sym(S.WHITESPACE),
        rep(
            cat(
                sym(S.OPERATION)
                | sym(S.IDENTIFIER)
                | sym(S.LITERAL)
                | sym(S.LOOP)
                | sym(S.BRANCH),
                sym(S.WHITESPACE),
            )
        ),
    ),
    S.BRANCH: cat(
        sym(S.IF),
        sym(S.FUNCTION_BODY),
        opt(cat(sym(S.ELSE), sym(S.FUNCTION_BODY))),
        sym(S.END),
    ),
    S.LOOP: cat(sym(S.WHILE), sym(S.FUNCTION_BODY), sym(S.END)),
    S.OPERATION: (  # TODO rewrite with RegexBasedParser
        lit("-")
        | lit("!=")
        | lit(".")
        | lit("*")
        | lit("/")
        | lit("\\n")
        | lit("%")
        | lit("+")
        | lit("<")
        | lit("<=")
        | lit("=")
        | lit(">")
        | lit(">=")
        | lit("and")
        | lit("drop")
        | lit("dup")
        | lit("not")
        | lit("or")
        | lit("over")
        | lit("rot")
        | lit("strlen")
        | lit("substr")
        | lit("swap")
    ),
    S.LITERAL: sym(S.BOOLEAN_LITERAL) | sym(S.INTEGER_LITERAL) | sym(S.STRING_LITERAL),
    S.STRING_LITERAL: RegexBasedParser('^"([^\\\\]|\\\\("|n|\\\\))*"'),
    S.INTEGER_LITERAL: RegexBasedParser("^[0-9]+"),
    S.WHITESPACE: rep(sym(S.WHITESPACE_CHAR)),
    S.WHITESPACE_CHAR: sym(S.SPACE) | sym(S.NEWLINE),
    S.IDENTIFIER: RegexBasedParser("^[a-z_]+"),
    S.BOOLEAN_LITERAL: lit("true") | lit("false"),
    # TODO consider getting rid of all these literal symbols and just inline them above
    S.SPACE: lit(" "),
    S.NEWLINE: lit("\n"),
    S.IF: lit("if"),
    S.END: lit("end"),
    S.WHILE: lit("while"),
    S.ELSE: lit("else"),
    S.DOUBLE_QUOTE: lit('"'),
}

ROOT_SYMBOL = S.FUNCTION_BODY


def new_tokenize(code: str) -> Optional[ParseTree]:  # pragma: nocover
    # NOTE Tests call new_tokenize_generic() directly
    return new_tokenize_generic(REWRITE_RULES, ROOT_SYMBOL, code, SymbolType)

from enum import IntEnum, auto
from typing import Dict, Optional

from lang.parser.generic import (
    ConcatenationParser,
    LiteralParser,
    OptionalParser,
    OrParser,
    Parser,
    ParseTree,
    RegexBasedParser,
    RepeatParser,
    SymbolParser,
    new_parse_generic,
)


class SymbolType(IntEnum):
    BOOLEAN_LITERAL = auto()
    BRANCH = auto()
    FILE = auto()
    FUNCTION_BODY = auto()
    FUNCTION_BODY_ITEM = auto()
    FUNCTION_DEFINITION = auto()
    IDENTIFIER = auto()
    INTEGER_LITERAL = auto()
    LITERAL = auto()
    LOOP = auto()
    OPERATION = auto()
    STRING_LITERAL = auto()
    WHITESPACE = auto()


OPERATOR_KEYWORDS = [
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

CONTROL_FLOW_KEYWORDS = [
    "begin",
    "else",
    "end",
    "false",
    "fn",
    "if",
    "true",
    "while",
]

KEYWORDS = CONTROL_FLOW_KEYWORDS + OPERATOR_KEYWORDS


REWRITE_RULES: Dict[IntEnum, Parser] = {
    SymbolType.BOOLEAN_LITERAL: LiteralParser("true") | LiteralParser("false"),
    SymbolType.INTEGER_LITERAL: RegexBasedParser("^[0-9]+"),
    SymbolType.STRING_LITERAL: RegexBasedParser('^"([^\\\\]|\\\\("|n|\\\\))*"'),
    SymbolType.IDENTIFIER: RegexBasedParser("^[a-z_]+", forbidden=KEYWORDS),
    SymbolType.LITERAL: SymbolParser(SymbolType.BOOLEAN_LITERAL)
    | SymbolParser(SymbolType.INTEGER_LITERAL)
    | SymbolParser(SymbolType.STRING_LITERAL),
    SymbolType.OPERATION: OrParser(*[LiteralParser(op) for op in OPERATOR_KEYWORDS]),
    SymbolType.WHITESPACE: RegexBasedParser("^[ \\n]+"),
    SymbolType.BRANCH: ConcatenationParser(
        LiteralParser("if"),
        OptionalParser(
            ConcatenationParser(
                SymbolParser(SymbolType.WHITESPACE),
                SymbolParser(SymbolType.FUNCTION_BODY),
            )
        ),
        SymbolParser(SymbolType.WHITESPACE),
        OptionalParser(
            ConcatenationParser(
                LiteralParser("else"),
                OptionalParser(
                    ConcatenationParser(
                        SymbolParser(SymbolType.WHITESPACE),
                        SymbolParser(SymbolType.FUNCTION_BODY),
                    )
                ),
                SymbolParser(SymbolType.WHITESPACE),
            )
        ),
        LiteralParser("end"),
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
        LiteralParser("end"),
    ),
    SymbolType.FUNCTION_BODY_ITEM: (
        SymbolParser(SymbolType.BRANCH)
        | SymbolParser(SymbolType.LOOP)
        | SymbolParser(SymbolType.OPERATION)
        | SymbolParser(SymbolType.IDENTIFIER)
        | SymbolParser(SymbolType.LITERAL)
    ),
    SymbolType.FUNCTION_BODY: ConcatenationParser(
        SymbolParser(SymbolType.FUNCTION_BODY_ITEM),
        RepeatParser(
            ConcatenationParser(
                SymbolParser(SymbolType.WHITESPACE),
                SymbolParser(SymbolType.FUNCTION_BODY_ITEM),
            ),
        ),
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
        LiteralParser("begin"),
        SymbolParser(SymbolType.WHITESPACE),
        OptionalParser(
            ConcatenationParser(
                SymbolParser(SymbolType.FUNCTION_BODY),
                SymbolParser(SymbolType.WHITESPACE),
            )
        ),
        LiteralParser("end"),
    ),
    SymbolType.FILE: ConcatenationParser(
        OptionalParser(SymbolParser(SymbolType.WHITESPACE)),
        SymbolParser(SymbolType.FUNCTION_DEFINITION),
        RepeatParser(
            ConcatenationParser(
                SymbolParser(SymbolType.WHITESPACE),
                SymbolParser(SymbolType.FUNCTION_DEFINITION),
            )
        ),
        OptionalParser(SymbolParser(SymbolType.WHITESPACE)),
    ),
}

ROOT_SYMBOL = SymbolType.FILE


def new_parse(code: str) -> Optional[ParseTree]:  # pragma: nocover
    # NOTE Tests call new_tokenize_generic() directly
    return new_parse_generic(REWRITE_RULES, ROOT_SYMBOL, code, SymbolType)

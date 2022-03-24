# ================================================================= #
#        THIS FILE WAS AUTOMATICALLY GENERATED, DO NOT EDIT!        #
# ================================================================= #

# This turns off formatting for flake8, pycln and black
# flake8: noqa
# fmt: off
# nopycln: file

from enum import IntEnum
from itertools import count
from parser.parser.models import (
    ConcatenationExpression,
    ConjunctionExpression,
    Expression,
    NonTerminalExpression,
    OptionalExpression,
    RepeatExpression,
    TerminalExpression,
    Tree,
)
from parser.parser.parser import Parser
from parser.tokenizer.models import Literal, Regex, Token, TokenDescriptor
from parser.tokenizer.tokenizer import Tokenizer
from typing import Dict, List, Optional, Set, Tuple

# We can't use enum.auto, since Terminal and NonTerminal will have colliding values
next_offset = count(start=1)


class Terminal(IntEnum):
    AND = next(next_offset)
    ARGS = next(next_offset)
    AS = next(next_offset)
    ASTERISK = next(next_offset)
    BACKSLASH_N = next(next_offset)
    BEGIN = next(next_offset)
    COMMA = next(next_offset)
    COMMENT = next(next_offset)
    DROP = next(next_offset)
    DUP = next(next_offset)
    ELSE = next(next_offset)
    END = next(next_offset)
    EQUALS = next(next_offset)
    FALSE = next(next_offset)
    FN = next(next_offset)
    GREATER_EQUALS = next(next_offset)
    GREATER_THAN = next(next_offset)
    IDENTIFIER = next(next_offset)
    IF = next(next_offset)
    INTEGER = next(next_offset)
    LESS_EQUALS = next(next_offset)
    LESS_THAN = next(next_offset)
    MINUS = next(next_offset)
    NOP = next(next_offset)
    NOT = next(next_offset)
    NOT_EQUALS = next(next_offset)
    OR = next(next_offset)
    OVER = next(next_offset)
    PERCENT = next(next_offset)
    PERIOD = next(next_offset)
    PLUS = next(next_offset)
    RETURN = next(next_offset)
    ROT = next(next_offset)
    SHEBANG = next(next_offset)
    SLASH = next(next_offset)
    STRING = next(next_offset)
    STRLEN = next(next_offset)
    SUBSTR = next(next_offset)
    SWAP = next(next_offset)
    TRUE = next(next_offset)
    WHILE = next(next_offset)
    WHITESPACE = next(next_offset)


TERMINAL_RULES: List[TokenDescriptor] = [
    Regex(Terminal.BEGIN, "begin(?=\\s|$)"),
    Regex(Terminal.ELSE, "else(?=\\s|$)"),
    Regex(Terminal.END, "end(?=\\s|$)"),
    Regex(Terminal.FN, "fn(?=\\s|$)"),
    Regex(Terminal.IF, "if(?=\\s|$)"),
    Regex(Terminal.WHILE, "while(?=\\s|$)"),
    Regex(Terminal.ARGS, "args(?=\\s|$)"),
    Regex(Terminal.AS, "as(?=\\s|$)"),
    Regex(Terminal.RETURN, "return(?=\\s|$)"),
    Regex(Terminal.AND, "and(?=\\s|$)"),
    Literal(Terminal.ASTERISK, "*"),
    Regex(Terminal.BACKSLASH_N, "\\\\n(?=\\s|$)"),
    Regex(Terminal.COMMA, ",(?=\\s|$)"),
    Regex(Terminal.DROP, "drop(?=\\s|$)"),
    Regex(Terminal.DUP, "dup(?=\\s|$)"),
    Regex(Terminal.EQUALS, "=(?=\\s|$)"),
    Regex(Terminal.GREATER_EQUALS, ">=(?=\\s|$)"),
    Regex(Terminal.GREATER_THAN, ">(?=\\s|$)"),
    Regex(Terminal.LESS_EQUALS, "<=(?=\\s|$)"),
    Regex(Terminal.LESS_THAN, "<(?=\\s|$)"),
    Regex(Terminal.MINUS, "-(?=\\s|$)"),
    Regex(Terminal.NOP, "nop(?=\\s|$)"),
    Regex(Terminal.NOT, "not(?=\\s|$)"),
    Regex(Terminal.NOT_EQUALS, "!=(?=\\s|$)"),
    Regex(Terminal.OR, "or(?=\\s|$)"),
    Regex(Terminal.OVER, "over(?=\\s|$)"),
    Regex(Terminal.PERCENT, "%(?=\\s|$)"),
    Regex(Terminal.PERIOD, "\\.(?=\\s|$)"),
    Regex(Terminal.PLUS, "\\+(?=\\s|$)"),
    Regex(Terminal.ROT, "rot(?=\\s|$)"),
    Regex(Terminal.SLASH, "/(?=\\s|$)"),
    Regex(Terminal.STRLEN, "strlen(?=\\s|$)"),
    Regex(Terminal.SUBSTR, "substr(?=\\s|$)"),
    Regex(Terminal.SWAP, "swap(?=\\s|$)"),
    Regex(Terminal.TRUE, "true(?=\\s|$)"),
    Regex(Terminal.FALSE, "false(?=\\s|$)"),
    Regex(Terminal.IDENTIFIER, "[a-z_]+"),
    Regex(Terminal.INTEGER, "[0-9]+"),
    Regex(Terminal.STRING, '"([^\\\\]|\\\\("|n|\\\\))*?"'),
    Regex(Terminal.WHITESPACE, "([ \n]|$)+"),
    Regex(Terminal.COMMENT, "//[^\n]*"),
    Regex(Terminal.SHEBANG, "#![^\n]*"),
]


class NonTerminal(IntEnum):
    ARGUMENT = next(next_offset)
    ARGUMENT_LIST = next(next_offset)
    BOOLEAN = next(next_offset)
    BRANCH = next(next_offset)
    FUNCTION_BODY = next(next_offset)
    FUNCTION_BODY_ITEM = next(next_offset)
    FUNCTION_DEFINITION = next(next_offset)
    LITERAL = next(next_offset)
    LOOP = next(next_offset)
    OPERATOR = next(next_offset)
    RETURN_TYPE = next(next_offset)
    RETURN_TYPES = next(next_offset)
    ROOT = next(next_offset)
    TYPED_ARGUMENT = next(next_offset)
    TYPE_PLACEHOLDER = next(next_offset)


NON_TERMINAL_RULES: Dict[IntEnum, Expression] = {
    NonTerminal.ARGUMENT: ConjunctionExpression(
        NonTerminalExpression(NonTerminal.TYPE_PLACEHOLDER),
        NonTerminalExpression(NonTerminal.TYPED_ARGUMENT),
    ),
    NonTerminal.ARGUMENT_LIST: ConcatenationExpression(
        NonTerminalExpression(NonTerminal.ARGUMENT),
        RepeatExpression(
            ConcatenationExpression(
                TerminalExpression(Terminal.COMMA),
                NonTerminalExpression(NonTerminal.ARGUMENT),
            )
        ),
    ),
    NonTerminal.BOOLEAN: ConjunctionExpression(
        TerminalExpression(Terminal.TRUE), TerminalExpression(Terminal.FALSE)
    ),
    NonTerminal.BRANCH: ConcatenationExpression(
        TerminalExpression(Terminal.IF),
        NonTerminalExpression(NonTerminal.FUNCTION_BODY),
        TerminalExpression(Terminal.BEGIN),
        NonTerminalExpression(NonTerminal.FUNCTION_BODY),
        OptionalExpression(
            ConcatenationExpression(
                TerminalExpression(Terminal.ELSE),
                NonTerminalExpression(NonTerminal.FUNCTION_BODY),
            )
        ),
        TerminalExpression(Terminal.END),
    ),
    NonTerminal.FUNCTION_BODY: ConcatenationExpression(
        NonTerminalExpression(NonTerminal.FUNCTION_BODY_ITEM),
        RepeatExpression(NonTerminalExpression(NonTerminal.FUNCTION_BODY_ITEM)),
    ),
    NonTerminal.FUNCTION_BODY_ITEM: ConjunctionExpression(
        NonTerminalExpression(NonTerminal.BRANCH),
        NonTerminalExpression(NonTerminal.LOOP),
        NonTerminalExpression(NonTerminal.OPERATOR),
        TerminalExpression(Terminal.IDENTIFIER),
        NonTerminalExpression(NonTerminal.LITERAL),
    ),
    NonTerminal.FUNCTION_DEFINITION: ConcatenationExpression(
        TerminalExpression(Terminal.FN),
        TerminalExpression(Terminal.IDENTIFIER),
        OptionalExpression(
            ConcatenationExpression(
                TerminalExpression(Terminal.ARGS),
                NonTerminalExpression(NonTerminal.ARGUMENT_LIST),
            )
        ),
        OptionalExpression(
            ConcatenationExpression(
                TerminalExpression(Terminal.RETURN),
                NonTerminalExpression(NonTerminal.RETURN_TYPES),
            )
        ),
        TerminalExpression(Terminal.BEGIN),
        NonTerminalExpression(NonTerminal.FUNCTION_BODY),
        TerminalExpression(Terminal.END),
    ),
    NonTerminal.LITERAL: ConjunctionExpression(
        NonTerminalExpression(NonTerminal.BOOLEAN),
        TerminalExpression(Terminal.INTEGER),
        TerminalExpression(Terminal.STRING),
    ),
    NonTerminal.LOOP: ConcatenationExpression(
        TerminalExpression(Terminal.WHILE),
        NonTerminalExpression(NonTerminal.FUNCTION_BODY),
        TerminalExpression(Terminal.BEGIN),
        NonTerminalExpression(NonTerminal.FUNCTION_BODY),
        TerminalExpression(Terminal.END),
    ),
    NonTerminal.OPERATOR: ConjunctionExpression(
        TerminalExpression(Terminal.AND),
        TerminalExpression(Terminal.ASTERISK),
        TerminalExpression(Terminal.BACKSLASH_N),
        TerminalExpression(Terminal.DROP),
        TerminalExpression(Terminal.DUP),
        TerminalExpression(Terminal.EQUALS),
        TerminalExpression(Terminal.GREATER_EQUALS),
        TerminalExpression(Terminal.GREATER_THAN),
        TerminalExpression(Terminal.LESS_EQUALS),
        TerminalExpression(Terminal.LESS_THAN),
        TerminalExpression(Terminal.MINUS),
        TerminalExpression(Terminal.NOP),
        TerminalExpression(Terminal.NOT),
        TerminalExpression(Terminal.NOT_EQUALS),
        TerminalExpression(Terminal.OR),
        TerminalExpression(Terminal.OVER),
        TerminalExpression(Terminal.PERCENT),
        TerminalExpression(Terminal.PERIOD),
        TerminalExpression(Terminal.PLUS),
        TerminalExpression(Terminal.ROT),
        TerminalExpression(Terminal.SLASH),
        TerminalExpression(Terminal.STRLEN),
        TerminalExpression(Terminal.SUBSTR),
        TerminalExpression(Terminal.SWAP),
    ),
    NonTerminal.RETURN_TYPE: ConjunctionExpression(
        TerminalExpression(Terminal.IDENTIFIER),
        NonTerminalExpression(NonTerminal.TYPE_PLACEHOLDER),
    ),
    NonTerminal.RETURN_TYPES: ConcatenationExpression(
        NonTerminalExpression(NonTerminal.RETURN_TYPE),
        RepeatExpression(
            ConcatenationExpression(
                TerminalExpression(Terminal.COMMA),
                NonTerminalExpression(NonTerminal.RETURN_TYPE),
            )
        ),
    ),
    NonTerminal.ROOT: RepeatExpression(
        NonTerminalExpression(NonTerminal.FUNCTION_DEFINITION)
    ),
    NonTerminal.TYPED_ARGUMENT: ConcatenationExpression(
        TerminalExpression(Terminal.IDENTIFIER),
        TerminalExpression(Terminal.AS),
        TerminalExpression(Terminal.IDENTIFIER),
    ),
    NonTerminal.TYPE_PLACEHOLDER: ConcatenationExpression(
        TerminalExpression(Terminal.ASTERISK), TerminalExpression(Terminal.IDENTIFIER)
    ),
}


PRUNED_TERMINALS: Set[IntEnum] = {
    Terminal.COMMENT,
    Terminal.SHEBANG,
    Terminal.WHITESPACE,
}


PRUNED_NON_TERMINALS: Set[IntEnum] = {
    NonTerminal.FUNCTION_BODY_ITEM,
    NonTerminal.LITERAL,
    NonTerminal.TYPED_ARGUMENT,
    NonTerminal.TYPE_PLACEHOLDER,
}


def parse(filename: str, code: str) -> Tuple[List[Token], Tree]:

    tokens: List[Token] = Tokenizer(
        filename=filename,
        code=code,
        terminal_rules=TERMINAL_RULES,
        pruned_terminals=PRUNED_TERMINALS,
    ).tokenize()

    tree: Tree = Parser(
        filename=filename,
        tokens=tokens,
        code=code,
        non_terminal_rules=NON_TERMINAL_RULES,
        pruned_non_terminals=PRUNED_NON_TERMINALS,
        root_token="ROOT",
    ).parse()

    return tokens, tree

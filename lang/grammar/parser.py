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
    ASTERISK = next(next_offset)
    BACKSLASH_N = next(next_offset)
    BEGIN = next(next_offset)
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
    ROT = next(next_offset)
    SLASH = next(next_offset)
    STRING = next(next_offset)
    STRLEN = next(next_offset)
    SUBSTR = next(next_offset)
    SWAP = next(next_offset)
    TRUE = next(next_offset)
    WHILE = next(next_offset)
    WHITESPACE = next(next_offset)


TERMINAL_RULES: List[TokenDescriptor] = [
    Literal(Terminal.BEGIN, "begin"),
    Literal(Terminal.ELSE, "else"),
    Literal(Terminal.END, "end"),
    Literal(Terminal.FN, "fn"),
    Literal(Terminal.IF, "if"),
    Literal(Terminal.WHILE, "while"),
    Literal(Terminal.AND, "and"),
    Literal(Terminal.ASTERISK, "*"),
    Literal(Terminal.BACKSLASH_N, "\\n"),
    Literal(Terminal.DROP, "drop"),
    Literal(Terminal.DUP, "dup"),
    Literal(Terminal.EQUALS, "="),
    Literal(Terminal.GREATER_EQUALS, ">="),
    Literal(Terminal.GREATER_THAN, ">"),
    Literal(Terminal.LESS_EQUALS, "<="),
    Literal(Terminal.LESS_THAN, "<"),
    Literal(Terminal.MINUS, "-"),
    Literal(Terminal.NOP, "nop"),
    Literal(Terminal.NOT, "not"),
    Literal(Terminal.NOT_EQUALS, "!="),
    Literal(Terminal.OR, "or"),
    Literal(Terminal.OVER, "over"),
    Literal(Terminal.PERCENT, "%"),
    Literal(Terminal.PERIOD, "."),
    Literal(Terminal.PLUS, "+"),
    Literal(Terminal.ROT, "rot"),
    Literal(Terminal.SLASH, "/"),
    Literal(Terminal.STRLEN, "strlen"),
    Literal(Terminal.SUBSTR, "substr"),
    Literal(Terminal.SWAP, "swap"),
    Literal(Terminal.TRUE, "true"),
    Literal(Terminal.FALSE, "false"),
    Regex(Terminal.IDENTIFIER, "[a-z_]+"),
    Regex(Terminal.INTEGER, "[0-9]+"),
    Regex(Terminal.STRING, '"([^\\\\]|\\\\("|n|\\\\))*?"'),
    Regex(Terminal.WHITESPACE, "([ \n]|$)+"),
]


class NonTerminal(IntEnum):
    BOOLEAN = next(next_offset)
    BRANCH = next(next_offset)
    FUNCTION_BODY = next(next_offset)
    FUNCTION_BODY_ITEM = next(next_offset)
    FUNCTION_DEFINITION = next(next_offset)
    FUNCTION_NAME_AND_ARGS = next(next_offset)
    LITERAL = next(next_offset)
    LOOP = next(next_offset)
    OPERATOR = next(next_offset)
    ROOT = next(next_offset)


NON_TERMINAL_RULES: Dict[IntEnum, Expression] = {
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
        NonTerminalExpression(NonTerminal.FUNCTION_NAME_AND_ARGS),
        TerminalExpression(Terminal.BEGIN),
        NonTerminalExpression(NonTerminal.FUNCTION_BODY),
        TerminalExpression(Terminal.END),
    ),
    NonTerminal.FUNCTION_NAME_AND_ARGS: ConcatenationExpression(
        TerminalExpression(Terminal.IDENTIFIER),
        RepeatExpression(TerminalExpression(Terminal.IDENTIFIER)),
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
    NonTerminal.ROOT: RepeatExpression(
        NonTerminalExpression(NonTerminal.FUNCTION_DEFINITION)
    ),
}


PRUNED_TERMINALS: Set[IntEnum] = {
    Terminal.WHITESPACE,
}


PRUNED_NON_TERMINALS: Set[IntEnum] = {
    NonTerminal.FUNCTION_BODY_ITEM,
    NonTerminal.LITERAL,
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

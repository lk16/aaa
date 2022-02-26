from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Dict, List, Optional, Union

from lang.parser.generic import (
    ConcatenationParser,
    LiteralParser,
    OptionalParser,
    OrParser,
    Parser,
    RegexBasedParser,
    RepeatParser,
    SymbolParser,
    SymbolTree,
    new_parse_generic,
)
from lang.parser.tree import prune_by_symbol_types, prune_useless, prune_zero_length


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
    BEGIN = auto()
    ELSE = auto()
    END = auto()
    FN = auto()
    IF = auto()
    WHILE = auto()
    # TODO add comments


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
    "false",
    "not",
    "or",
    "over",
    "rot",
    "strlen",
    "substr",
    "swap",
    "true",
]

CONTROL_FLOW_KEYWORDS = [
    "begin",
    "else",
    "end",
    "fn",
    "if",
    "while",
]

KEYWORDS = CONTROL_FLOW_KEYWORDS + OPERATOR_KEYWORDS


# NOTE A more readable grammar can be found in grammar.txt in the repo root.
REWRITE_RULES: Dict[IntEnum, Parser] = {
    SymbolType.BEGIN: LiteralParser("begin"),
    SymbolType.ELSE: LiteralParser("else"),
    SymbolType.END: LiteralParser("end"),
    SymbolType.FN: LiteralParser("fn"),
    SymbolType.IF: LiteralParser("if"),
    SymbolType.WHILE: LiteralParser("while"),
    SymbolType.BOOLEAN_LITERAL: OrParser(LiteralParser("true"), LiteralParser("false")),
    SymbolType.INTEGER_LITERAL: RegexBasedParser("^[0-9]+"),
    SymbolType.STRING_LITERAL: RegexBasedParser('^"([^\\\\]|\\\\("|n|\\\\))*"'),
    SymbolType.IDENTIFIER: RegexBasedParser("^[a-z_]+", forbidden=KEYWORDS),
    SymbolType.LITERAL: OrParser(
        SymbolParser(SymbolType.BOOLEAN_LITERAL),
        SymbolParser(SymbolType.INTEGER_LITERAL),
        SymbolParser(SymbolType.STRING_LITERAL),
    ),
    SymbolType.OPERATION: OrParser(*[LiteralParser(op) for op in OPERATOR_KEYWORDS]),
    SymbolType.WHITESPACE: RegexBasedParser("^([ \\n]|$)+"),
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
    SymbolType.FUNCTION_BODY_ITEM: OrParser(
        SymbolParser(SymbolType.BRANCH),
        SymbolParser(SymbolType.LOOP),
        SymbolParser(SymbolType.OPERATION),
        SymbolParser(SymbolType.IDENTIFIER),
        SymbolParser(SymbolType.LITERAL),
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
        SymbolParser(SymbolType.FN),
        SymbolParser(SymbolType.WHITESPACE),
        RepeatParser(
            ConcatenationParser(
                SymbolParser(SymbolType.IDENTIFIER), SymbolParser(SymbolType.WHITESPACE)
            ),
            min_repeats=1,
        ),
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
    SymbolType.FILE: ConcatenationParser(
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
}

ROOT_SYMBOL = SymbolType.FILE


class EmptyParseTreeError(Exception):
    ...


FunctionBodyItem = Union[
    "Branch", "Loop", "Operation", "BooleanLiteral", "IntegerLiteral", "StringLiteral"
]


@dataclass
class IntegerLiteral:
    value: int

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "IntegerLiteral":
        raise NotImplementedError


@dataclass
class StringLiteral:
    value: str

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "StringLiteral":
        raise NotImplementedError


@dataclass
class BooleanLiteral:
    value: bool

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "BooleanLiteral":
        raise NotImplementedError


@dataclass
class Operation:
    operator: str

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "Operation":
        raise NotImplementedError


@dataclass
class Loop:
    loop_body: List[FunctionBodyItem]

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "Loop":
        raise NotImplementedError


@dataclass
class Branch:
    if_body: List[FunctionBodyItem]
    else_body: Optional[List[FunctionBodyItem]]

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "Branch":
        raise NotImplementedError


@dataclass
class Function:
    name: str
    arguments: List[str]
    body: List[FunctionBodyItem]

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "Function":
        assert tree.symbol_type == SymbolType.FUNCTION_DEFINITION

        name, *arguments = [
            child.children[0].value(code) for child in tree.children[1].children
        ]

        body: List[FunctionBodyItem] = []
        # TODO

        return Function(name, arguments, body)


@dataclass
class File:
    functions: List[Function]

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "File":
        assert tree.symbol_type == SymbolType.FILE

        functions: List[Function] = []

        for child in tree.children[0].children:
            functions.append(Function.from_symboltree(child.children[0], code))

        return File(functions)


def parse(code: str) -> File:

    # NOTE Tests call new_tokenize_generic() directly
    tree: Optional[SymbolTree] = new_parse_generic(
        REWRITE_RULES, ROOT_SYMBOL, code, SymbolType
    )

    if tree:
        tree = prune_zero_length(tree)

    if tree:
        tree = prune_by_symbol_types(tree, {SymbolType.WHITESPACE})

    if tree:
        tree = prune_useless(tree)

    if not tree:
        raise EmptyParseTreeError

    return File.from_symboltree(tree, code)

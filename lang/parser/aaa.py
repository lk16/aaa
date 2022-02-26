from abc import abstractclassmethod
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Dict, List, Optional, Type, Union

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
from lang.parser.symbol_tree import (
    prune_by_symbol_types,
    prune_useless,
    prune_zero_length,
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
class AaaTreeNode:
    @abstractclassmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "AaaTreeNode":
        ...


@dataclass
class IntegerLiteral(AaaTreeNode):
    value: int

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "IntegerLiteral":
        assert tree.symbol_type == SymbolType.INTEGER_LITERAL
        value = int(tree.value(code))
        return IntegerLiteral(value)


@dataclass
class StringLiteral(AaaTreeNode):
    value: str

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "StringLiteral":
        raise NotImplementedError


@dataclass
class BooleanLiteral(AaaTreeNode):
    value: bool

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "BooleanLiteral":
        assert tree.symbol_type == SymbolType.BOOLEAN_LITERAL
        value = tree.value(code) == "true"
        return BooleanLiteral(value)


@dataclass
class Operation(AaaTreeNode):
    operator: str

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "Operation":
        assert tree.symbol_type == SymbolType.OPERATION
        operator = tree.value(code)
        return Operation(operator)


@dataclass
class Loop(AaaTreeNode):
    loop_body: List[FunctionBodyItem]

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "Loop":
        raise NotImplementedError


@dataclass
class Branch(AaaTreeNode):
    if_body: "FunctionBody"
    else_body: "FunctionBody"

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "Branch":
        if_body = FunctionBody([])
        else_body = FunctionBody([])

        for child in tree.children:
            if child.symbol_type in [SymbolType.IF, SymbolType.END]:
                continue
            elif (
                child.symbol_type is None
                and child.children[0].symbol_type == SymbolType.ELSE
            ):
                if len(child.children) > 1:
                    else_body = FunctionBody.from_symboltree(
                        child.children[1].children[0], code
                    )
            else:
                if_body = FunctionBody.from_symboltree(child.children[0], code)

        return Branch(if_body, else_body)


@dataclass
class FunctionBody(AaaTreeNode):
    items: List[FunctionBodyItem]

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "FunctionBody":
        assert tree.symbol_type == SymbolType.FUNCTION_BODY

        aaa_tree_nodes: Dict[Optional[IntEnum], Type[FunctionBodyItem]] = {
            SymbolType.BRANCH: Branch,
            SymbolType.LOOP: Loop,
            SymbolType.OPERATION: Operation,
            SymbolType.INTEGER_LITERAL: IntegerLiteral,
            SymbolType.STRING_LITERAL: StringLiteral,
            SymbolType.BOOLEAN_LITERAL: BooleanLiteral,
        }

        flattened_children: List[SymbolTree] = []

        if len(tree.children) > 0:
            flattened_children = [tree.children[0]]

        if len(tree.children) > 1:
            flattened_children += [
                child.children[0] for child in tree.children[1].children
            ]

        items: List[FunctionBodyItem] = []

        for child in flattened_children:
            aaa_tree_node = aaa_tree_nodes[child.symbol_type]
            items.append(aaa_tree_node.from_symboltree(child, code))

        return FunctionBody(items)


@dataclass
class Function(AaaTreeNode):
    name: str
    arguments: List[str]
    body: FunctionBody

    @classmethod
    def from_symboltree(cls, tree: SymbolTree, code: str) -> "Function":
        assert tree.symbol_type == SymbolType.FUNCTION_DEFINITION

        name, *arguments = [
            child.children[0].value(code) for child in tree.children[1].children
        ]

        if tree.children[3].symbol_type == SymbolType.END:
            body = FunctionBody([])
        else:
            body = FunctionBody.from_symboltree(tree.children[3].children[0], code)

        return Function(name, arguments, body)


@dataclass
class File(AaaTreeNode):
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

from abc import abstractclassmethod
from dataclasses import dataclass
from enum import IntEnum
from parser.generic import Tree, new_parse_generic
from parser.tree import prune_by_symbol_types, prune_useless, prune_zero_length
from typing import Dict, List, Optional, Type, Union

from lang.exceptions import EmptyParseTreeError
from lang.grammar import REWRITE_RULES, ROOT_SYMBOL, SymbolType
from lang.instructions import Instruction, get_function_instructions

FunctionBodyItem = Union[
    "Branch",
    "Loop",
    "Operation",
    "BooleanLiteral",
    "IntegerLiteral",
    "StringLiteral",
    "Identifier",
]


@dataclass
class AaaTreeNode:
    @abstractclassmethod
    def from_tree(cls, tree: Tree, code: str) -> "AaaTreeNode":
        ...


@dataclass
class IntegerLiteral(AaaTreeNode):
    value: int

    @classmethod
    def from_tree(cls, tree: Tree, code: str) -> "IntegerLiteral":
        assert tree.symbol_type == SymbolType.INTEGER_LITERAL
        value = int(tree.value(code))
        return IntegerLiteral(value)


@dataclass
class StringLiteral(AaaTreeNode):
    value: str

    @classmethod
    def from_tree(cls, tree: Tree, code: str) -> "StringLiteral":
        assert tree.symbol_type == SymbolType.STRING_LITERAL
        value = (
            tree.value(code)[1:-1]
            .replace("\\n", "\n")
            .replace('\\"', '"')
            .replace("\\\\", "\\")
        )
        return StringLiteral(value)


@dataclass
class BooleanLiteral(AaaTreeNode):
    value: bool

    @classmethod
    def from_tree(cls, tree: Tree, code: str) -> "BooleanLiteral":
        assert tree.symbol_type == SymbolType.BOOLEAN_LITERAL
        value = tree.value(code) == "true"
        return BooleanLiteral(value)


@dataclass
class Operation(AaaTreeNode):
    operator: str

    @classmethod
    def from_tree(cls, tree: Tree, code: str) -> "Operation":
        assert tree.symbol_type == SymbolType.OPERATION
        operator = tree.value(code)
        return Operation(operator)


@dataclass
class Loop(AaaTreeNode):
    body: "FunctionBody"

    @classmethod
    def from_tree(cls, tree: Tree, code: str) -> "Loop":
        loop_body = FunctionBody([])

        if tree.children[1].symbol_type != SymbolType.END:
            loop_body = FunctionBody.from_tree(tree.children[1].children[0], code)

        return Loop(loop_body)


@dataclass
class Identifier(AaaTreeNode):
    name: str

    @classmethod
    def from_tree(cls, tree: Tree, code: str) -> "Identifier":
        name = tree.value(code)
        return Identifier(name)


@dataclass
class Branch(AaaTreeNode):
    if_body: "FunctionBody"
    else_body: "FunctionBody"

    @classmethod
    def from_tree(cls, tree: Tree, code: str) -> "Branch":
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
                    else_body = FunctionBody.from_tree(
                        child.children[1].children[0], code
                    )
            else:
                if_body = FunctionBody.from_tree(child.children[0], code)

        return Branch(if_body, else_body)


@dataclass
class FunctionBody(AaaTreeNode):
    items: List[FunctionBodyItem]

    @classmethod
    def from_tree(cls, tree: Tree, code: str) -> "FunctionBody":
        assert tree.symbol_type == SymbolType.FUNCTION_BODY

        aaa_tree_nodes: Dict[Optional[IntEnum], Type[FunctionBodyItem]] = {
            SymbolType.BOOLEAN_LITERAL: BooleanLiteral,
            SymbolType.BRANCH: Branch,
            SymbolType.IDENTIFIER: Identifier,
            SymbolType.INTEGER_LITERAL: IntegerLiteral,
            SymbolType.LOOP: Loop,
            SymbolType.OPERATION: Operation,
            SymbolType.STRING_LITERAL: StringLiteral,
        }

        flattened_children: List[Tree] = []

        if len(tree.children) > 0:
            flattened_children = [tree.children[0]]

        if len(tree.children) > 1:
            flattened_children += [
                child.children[0] for child in tree.children[1].children
            ]

        items: List[FunctionBodyItem] = []

        for child in flattened_children:
            aaa_tree_node = aaa_tree_nodes[child.symbol_type]
            items.append(aaa_tree_node.from_tree(child, code))

        return FunctionBody(items)


@dataclass
class Function(AaaTreeNode):
    name: str
    arguments: List[str]
    body: FunctionBody
    _instructions: Optional[List[Instruction]] = None

    @classmethod
    def from_tree(cls, tree: Tree, code: str) -> "Function":
        assert tree.symbol_type == SymbolType.FUNCTION_DEFINITION

        name, *arguments = [
            child.children[0].value(code) for child in tree.children[1].children
        ]

        if tree.children[3].symbol_type == SymbolType.END:
            body = FunctionBody([])
        else:
            body = FunctionBody.from_tree(tree.children[3].children[0], code)

        return Function(name, arguments, body)

    def get_instructions(self) -> List[Instruction]:
        if self._instructions is None:
            self._instructions = get_function_instructions(self)

        return self._instructions


@dataclass
class File(AaaTreeNode):
    functions: List[Function]

    @classmethod
    def from_tree(cls, tree: Tree, code: str) -> "File":
        assert tree.symbol_type == SymbolType.FILE

        functions: List[Function] = []

        for child in tree.children[0].children:
            functions.append(Function.from_tree(child.children[0], code))

        return File(functions)


def parse(code: str) -> File:
    tree: Optional[Tree] = new_parse_generic(
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

    return File.from_tree(tree, code)

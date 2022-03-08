from abc import abstractclassmethod
from dataclasses import dataclass
from enum import IntEnum
from parser.parser import Tree
from typing import Dict, List, Optional, Type, Union

from lang.exceptions import FunctionNameCollission, InvalidFunctionArgumentList
from lang.grammar.parser import SymbolType
from lang.grammar.parser import parse as parse_aaa
from lang.instruction_types import Instruction

FunctionBodyItem = Union[
    "Branch",
    "Loop",
    "Operator",
    "BooleanLiteral",
    "IntegerLiteral",
    "StringLiteral",
    "Identifier",
]


class AaaTreeNode:
    @abstractclassmethod
    def from_tree(cls, tree: Tree, code: str) -> "AaaTreeNode":  # pragma: nocover
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
class Operator(AaaTreeNode):
    value: str

    @classmethod
    def from_tree(cls, tree: Tree, code: str) -> "Operator":
        assert tree.symbol_type in [
            SymbolType.OPERATOR_NON_ALPHABETICAL,
            SymbolType.OPERATOR_KEYWORD,
        ]
        operator = tree.value(code)
        return Operator(operator)


@dataclass
class Loop(AaaTreeNode):
    body: "FunctionBody"

    @classmethod
    def from_tree(cls, tree: Tree, code: str) -> "Loop":
        assert tree.symbol_type == SymbolType.LOOP

        if len(tree.children) == 1 and tree[0].symbol_type == SymbolType.LOOP:
            # TODO this is an ugly hack to bypass bugs likely in parser lib
            tree = tree[0]

        loop_body = FunctionBody.from_tree(tree.children[0], code)
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
        assert tree.symbol_type == SymbolType.BRANCH

        if len(tree.children) == 1 and tree[0].symbol_type == SymbolType.BRANCH:
            # TODO this is an ugly hack to bypass bugs likely in parser lib
            tree = tree[0]

        if_body = FunctionBody.from_tree(tree[0], code)

        if len(tree.children) == 2:
            else_body = FunctionBody.from_tree(tree[1], code)
        else:
            else_body = FunctionBody([])

        return Branch(if_body, else_body)


@dataclass
class FunctionBody(AaaTreeNode):
    items: List[FunctionBodyItem]

    @classmethod
    def from_tree(cls, tree: Tree, code: str) -> "FunctionBody":
        assert tree.symbol_type == SymbolType.FUNCTION_BODY

        if len(tree.children) == 1 and tree[0].symbol_type == SymbolType.FUNCTION_BODY:
            # TODO this is an ugly hack to bypass bugs likely in parser lib
            tree = tree[0]

        aaa_tree_nodes: Dict[Optional[IntEnum], Type[FunctionBodyItem]] = {
            SymbolType.BOOLEAN_LITERAL: BooleanLiteral,
            SymbolType.BRANCH: Branch,
            SymbolType.IDENTIFIER: Identifier,
            SymbolType.INTEGER_LITERAL: IntegerLiteral,
            SymbolType.LOOP: Loop,
            SymbolType.OPERATOR_KEYWORD: Operator,
            SymbolType.OPERATOR_NON_ALPHABETICAL: Operator,
            SymbolType.STRING_LITERAL: StringLiteral,
        }

        items: List[FunctionBodyItem] = []

        for child in tree.children:
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

        if (
            len(tree.children) == 1
            and tree[0].symbol_type == SymbolType.FUNCTION_DEFINITION
        ):
            # TODO this is an ugly hack to bypass bugs likely in parser lib
            tree = tree[0]

        name, *arguments = [identifier.value(code) for identifier in tree[0].children]

        if len([name] + arguments) != len({name} | {*arguments}):
            raise InvalidFunctionArgumentList(name, arguments)

        body = FunctionBody.from_tree(tree[1], code)

        return Function(name, arguments, body)


@dataclass
class File(AaaTreeNode):
    functions: Dict[str, Function]

    @classmethod
    def from_tree(cls, tree: Tree, code: str) -> "File":
        assert tree.symbol_type == SymbolType.ROOT

        functions: Dict[str, Function] = {}

        for child in tree.children:
            function = Function.from_tree(child, code)

            if function.name in functions:
                raise FunctionNameCollission(function.name)

            functions[function.name] = function

        return File(functions)


def parse(code: str) -> File:
    tree: Optional[Tree] = parse_aaa(code)
    return File.from_tree(tree, code)

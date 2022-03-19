from abc import abstractclassmethod
from dataclasses import dataclass
from enum import IntEnum
from parser.parser.models import Tree
from parser.tokenizer.models import Token
from typing import Dict, List, Optional, Type, Union

from lang.exceptions import FunctionNameCollission, InvalidFunctionArgumentList
from lang.grammar.parser import NonTerminal, Terminal
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
    def from_tree(
        cls, tree: Tree, tokens: List[Token], code: str
    ) -> "AaaTreeNode":  # pragma: nocover
        ...


@dataclass
class IntegerLiteral(AaaTreeNode):
    value: int

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "IntegerLiteral":
        assert tree.token_type == Terminal.INTEGER
        value = int(tree.value(tokens, code))
        return IntegerLiteral(value)


@dataclass
class StringLiteral(AaaTreeNode):
    value: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "StringLiteral":
        assert tree.token_type == Terminal.STRING
        value = (
            tree.value(tokens, code)[1:-1]
            .replace("\\n", "\n")
            .replace('\\"', '"')
            .replace("\\\\", "\\")
        )
        return StringLiteral(value)


@dataclass
class BooleanLiteral(AaaTreeNode):
    value: bool

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "BooleanLiteral":
        assert tree.token_type == NonTerminal.BOOLEAN
        value = tree.value(tokens, code) == "true"
        return BooleanLiteral(value)


@dataclass
class Operator(AaaTreeNode):
    value: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Operator":
        assert tree.token_type == NonTerminal.OPERATOR
        operator = tree.value(tokens, code)
        return Operator(operator)


@dataclass
class Loop(AaaTreeNode):
    condition: "FunctionBody"
    body: "FunctionBody"

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Loop":
        assert tree.token_type == NonTerminal.LOOP

        if len(tree.children) == 1 and tree[0].token_type == NonTerminal.LOOP:
            # TODO this is an ugly hack to bypass bugs likely in parser lib
            tree = tree[0]

        condition = FunctionBody.from_tree(tree.children[1], tokens, code)
        loop_body = FunctionBody.from_tree(tree.children[3], tokens, code)
        return Loop(condition, loop_body)


@dataclass
class Identifier(AaaTreeNode):
    name: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Identifier":
        name = tree.value(tokens, code)
        return Identifier(name)


@dataclass
class Branch(AaaTreeNode):
    condition: "FunctionBody"
    if_body: "FunctionBody"
    else_body: "FunctionBody"

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Branch":
        assert tree.token_type == NonTerminal.BRANCH

        if len(tree.children) == 1 and tree[0].token_type == NonTerminal.BRANCH:
            # TODO this is an ugly hack to bypass bugs likely in parser lib
            tree = tree[0]

        condition = FunctionBody.from_tree(tree[1], tokens, code)

        if_body = FunctionBody.from_tree(tree[3], tokens, code)

        if len(tree.children) == 7:
            else_body = FunctionBody.from_tree(tree[5], tokens, code)
        else:
            else_body = FunctionBody([])

        return Branch(condition, if_body, else_body)


@dataclass
class FunctionBody(AaaTreeNode):
    items: List[FunctionBodyItem]

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "FunctionBody":
        assert tree.token_type == NonTerminal.FUNCTION_BODY

        if len(tree.children) == 1 and tree[0].token_type == NonTerminal.FUNCTION_BODY:
            # TODO this is an ugly hack to bypass bugs likely in parser lib
            tree = tree[0]

        aaa_tree_nodes: Dict[Optional[IntEnum], Type[FunctionBodyItem]] = {
            NonTerminal.BOOLEAN: BooleanLiteral,
            NonTerminal.BRANCH: Branch,
            Terminal.IDENTIFIER: Identifier,
            Terminal.INTEGER: IntegerLiteral,
            NonTerminal.LOOP: Loop,
            NonTerminal.OPERATOR: Operator,
            Terminal.STRING: StringLiteral,
        }

        items: List[FunctionBodyItem] = []

        for child in tree.children:
            aaa_tree_node = aaa_tree_nodes[child.token_type]
            items.append(aaa_tree_node.from_tree(child, tokens, code))

        return FunctionBody(items)


@dataclass
class Function(AaaTreeNode):
    name: str
    arguments: List[str]
    body: FunctionBody
    _instructions: Optional[List[Instruction]] = None

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Function":
        assert tree.token_type == NonTerminal.FUNCTION_DEFINITION

        if (
            len(tree.children) == 1
            and tree[0].token_type == NonTerminal.FUNCTION_DEFINITION
        ):
            # TODO this is an ugly hack to bypass bugs likely in parser lib
            tree = tree[0]

        name, *arguments = [
            identifier.value(tokens, code) for identifier in tree[1].children
        ]

        if len([name] + arguments) != len({name} | {*arguments}):
            raise InvalidFunctionArgumentList(name, arguments)

        body = FunctionBody.from_tree(tree[3], tokens, code)

        return Function(name, arguments, body)


@dataclass
class File(AaaTreeNode):
    functions: Dict[str, Function]

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "File":
        assert tree.token_type == NonTerminal.ROOT

        functions: Dict[str, Function] = {}

        for child in tree.children:
            function = Function.from_tree(child, tokens, code)

            if function.name in functions:
                raise FunctionNameCollission(function.name)

            functions[function.name] = function

        return File(functions)


def parse(filename: str, code: str) -> File:
    tokens, tree = parse_aaa(filename, code)
    return File.from_tree(tree, tokens, code)

from abc import abstractclassmethod
from dataclasses import dataclass
from enum import IntEnum
from parser.parser.models import Tree
from parser.tokenizer.models import Token
from typing import Dict, List, Optional, Type, Union

from lang.exceptions import FunctionNameCollission
from lang.grammar.parser import NonTerminal, Terminal
from lang.grammar.parser import parse as parse_aaa
from lang.instruction_types import Instruction
from lang.typing.signatures import IDENTIFIER_TO_TYPE, SignatureItem, SomeType

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
class Argument(AaaTreeNode):
    name: str
    type: SignatureItem

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Argument":
        assert tree.token_type == NonTerminal.ARGUMENT

        if tree[0].token_type == Terminal.IDENTIFIER:
            type_identifier = tree[2].value(tokens, code)
            try:
                type = IDENTIFIER_TO_TYPE[type_identifier]
            except KeyError:
                raise NotImplementedError

            return Argument(
                name=tree[0].value(tokens, code),
                type=type,
            )

        elif tree[0].token_type == Terminal.ASTERISK:
            type_placeholder = tree[1].value(tokens, code)

            return Argument(
                name=tree[1].value(tokens, code),
                type=SomeType(type_placeholder),
            )

        else:  # pragma: nocover
            assert False


@dataclass
class ReturnType(AaaTreeNode):
    type: SignatureItem

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "ReturnType":
        assert tree.token_type == NonTerminal.RETURN_TYPE

        if tree[0].token_type == Terminal.IDENTIFIER:
            type_identifier = tree[0].value(tokens, code)
            try:
                type = IDENTIFIER_TO_TYPE[type_identifier]
            except KeyError:
                raise NotImplementedError

            return ReturnType(type)

        elif tree[0].token_type == Terminal.ASTERISK:
            type_placeholder = tree[1].value(tokens, code)
            some_type = SomeType(type_placeholder)

            return ReturnType(some_type)
        else:  # pragma: nocover
            assert False


@dataclass
class Function(AaaTreeNode):
    name: str
    arguments: List[Argument]
    return_types: List[ReturnType]
    body: FunctionBody
    _instructions: Optional[List[Instruction]] = None

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Function":
        assert tree.token_type == NonTerminal.FUNCTION_DEFINITION

        func_name = tree[1].value(tokens, code)
        arguments: List[Argument] = []
        return_types: List[ReturnType] = []

        index = 2

        while True:
            token_type = tree[index].token_type

            if token_type == Terminal.ARGS:
                arguments = [
                    Argument.from_tree(child, tokens, code)
                    for child in tree[index + 1].children
                    if child.token_type != Terminal.COMMA
                ]

                # TODO check InvalidFunctionArgumentList

            elif token_type == Terminal.RETURN:
                return_types = [
                    ReturnType.from_tree(child, tokens, code)
                    for child in tree[index + 1].children
                    if child.token_type != Terminal.COMMA
                ]

            elif token_type == Terminal.BEGIN:
                body = FunctionBody.from_tree(tree[index + 1], tokens, code)
                break

            index += 2

        return Function(func_name, arguments, return_types, body)


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

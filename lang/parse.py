from abc import abstractclassmethod
from dataclasses import dataclass
from enum import IntEnum
from parser.parser.models import Tree
from parser.tokenizer.models import Token
from typing import Dict, List, Optional, Set, Type, Union

from lang.grammar.parser import NonTerminal, Terminal
from lang.instructions.types import Instruction
from lang.typing.exceptions import UnknownPlaceholderTypes, UnkonwnType
from lang.typing.signatures import (
    IDENTIFIER_TO_TYPE,
    PlaceholderType,
    Signature,
    SignatureItem,
)

FunctionBodyItem = Union[
    "Branch",
    "Loop",
    "Operator",
    "BooleanLiteral",
    "IntegerLiteral",
    "StringLiteral",
    "Identifier",
]


@dataclass(kw_only=True)
class AaaTreeNode:
    @abstractclassmethod
    def from_tree(
        cls, tree: Tree, tokens: List[Token], code: str
    ) -> "AaaTreeNode":  # pragma: nocover
        ...


@dataclass(kw_only=True)
class IntegerLiteral(AaaTreeNode):
    value: int

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "IntegerLiteral":
        assert tree.token_type == Terminal.INTEGER
        value = int(tree.value(tokens, code))
        return IntegerLiteral(value=value)


@dataclass(kw_only=True)
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
        return StringLiteral(value=value)


@dataclass(kw_only=True)
class BooleanLiteral(AaaTreeNode):
    value: bool

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "BooleanLiteral":
        assert tree.token_type == NonTerminal.BOOLEAN
        value = tree.value(tokens, code) == "true"
        return BooleanLiteral(value=value)


@dataclass(kw_only=True)
class Operator(AaaTreeNode):
    value: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Operator":
        assert tree.token_type == NonTerminal.OPERATOR
        operator = tree.value(tokens, code)
        return Operator(value=operator)


@dataclass(kw_only=True)
class Loop(AaaTreeNode):
    condition: "FunctionBody"
    body: "FunctionBody"

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Loop":
        assert tree.token_type == NonTerminal.LOOP

        condition = FunctionBody.from_tree(tree.children[1], tokens, code)
        loop_body = FunctionBody.from_tree(tree.children[3], tokens, code)
        return Loop(condition=condition, body=loop_body)


@dataclass(kw_only=True)
class Identifier(AaaTreeNode):
    name: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Identifier":
        name = tree.value(tokens, code)
        return Identifier(name=name)


@dataclass(kw_only=True)
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
            else_body = FunctionBody(items=[])

        return Branch(condition=condition, if_body=if_body, else_body=else_body)


@dataclass(kw_only=True)
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

        return FunctionBody(items=items)


@dataclass(kw_only=True)
class Argument(AaaTreeNode):
    name: str
    type: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Argument":
        assert tree.token_type == NonTerminal.ARGUMENT

        if tree[0].token_type == Terminal.IDENTIFIER:
            return Argument(
                name=tree[0].value(tokens, code),
                type=tree[2].value(tokens, code),
            )

        elif tree[0].token_type == Terminal.ASTERISK:
            return Argument(
                name=tree[1].value(tokens, code),
                type="*" + tree[1].value(tokens, code),
            )

        else:  # pragma: nocover
            assert False


@dataclass(kw_only=True)
class ReturnType(AaaTreeNode):
    type: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "ReturnType":
        assert tree.token_type == NonTerminal.RETURN_TYPE

        if tree[0].token_type == Terminal.IDENTIFIER:
            return ReturnType(type=tree[0].value(tokens, code))

        elif tree[0].token_type == Terminal.ASTERISK:
            return ReturnType(type="*" + tree[1].value(tokens, code))

        else:  # pragma: nocover
            assert False


@dataclass(kw_only=True)
class Function(AaaTreeNode):
    name: str
    arguments: List[Argument]
    return_types: List[ReturnType]
    body: FunctionBody
    _instructions: Optional[List[Instruction]] = None

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Function":
        assert tree.token_type == NonTerminal.FUNCTION_DEFINITION

        name = tree[1].value(tokens, code)
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

        return Function(
            name=name, arguments=arguments, return_types=return_types, body=body
        )

    def get_signature(self) -> Signature:
        # TODO move to Program and refactor this function

        placeholder_args: Set[str] = set()

        arg_types: List[SignatureItem] = []
        for arg_type in self.arguments:
            if arg_type.type.startswith("*"):
                arg_types.append(PlaceholderType(arg_type.name))
                placeholder_args.add(arg_type.type)
            else:
                try:
                    type = IDENTIFIER_TO_TYPE[arg_type.type]
                except KeyError as e:
                    raise UnkonwnType from e
                arg_types.append(type)

        return_types: List[SignatureItem] = []
        for return_type in self.return_types:
            if return_type.type.startswith("*"):
                if return_type.type not in placeholder_args:
                    raise UnknownPlaceholderTypes
                return_types.append(PlaceholderType(return_type.type[1:]))
            else:
                try:
                    type = IDENTIFIER_TO_TYPE[return_type.type]
                except KeyError as e:
                    raise UnkonwnType from e
                return_types.append(type)

        return Signature(arg_types, return_types)


@dataclass(kw_only=True)
class ParsedFile(AaaTreeNode):
    functions: List[Function]

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "ParsedFile":
        assert tree.token_type == NonTerminal.ROOT

        functions: List[Function] = []

        for child in tree.children:
            function = Function.from_tree(child, tokens, code)
            functions.append(function)

        return ParsedFile(functions=functions)

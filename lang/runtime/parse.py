from abc import abstractclassmethod
from dataclasses import dataclass
from enum import IntEnum
from parser.parser.models import Tree
from parser.tokenizer.models import Token
from typing import Dict, List, Optional, Type, Union

from lang.grammar.parser import NonTerminal, Terminal

FunctionBodyItem = Union[
    "Branch",
    "Loop",
    "Operator",
    "BooleanLiteral",
    "IntegerLiteral",
    "StringLiteral",
    "Identifier",
    "TypeLiteral",
]


@dataclass(kw_only=True)
class AaaTreeNode:
    token_offset: int
    token_count: int

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
        return IntegerLiteral(
            value=value, token_count=tree.token_count, token_offset=tree.token_offset
        )


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
        return StringLiteral(
            value=value, token_count=tree.token_count, token_offset=tree.token_offset
        )


@dataclass(kw_only=True)
class BooleanLiteral(AaaTreeNode):
    value: bool

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "BooleanLiteral":
        assert tree.token_type == NonTerminal.BOOLEAN
        value = tree.value(tokens, code) == "true"
        return BooleanLiteral(
            value=value, token_count=tree.token_count, token_offset=tree.token_offset
        )


@dataclass(kw_only=True)
class TypeLiteral(AaaTreeNode):
    type_name: str
    type_parameters: List["TypeLiteral"]

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "TypeLiteral":
        assert tree.token_type == NonTerminal.TYPE_LITERAL
        type_name = tree[0].value(tokens, code)

        # TODO type params are not implemented yet here
        assert len(tree.children) == 1
        type_parameters: List["TypeLiteral"] = []

        return TypeLiteral(
            type_name=type_name,
            type_parameters=type_parameters,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class Operator(AaaTreeNode):
    value: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Operator":
        assert tree.token_type == NonTerminal.OPERATOR
        operator = tree.value(tokens, code)
        return Operator(
            value=operator, token_count=tree.token_count, token_offset=tree.token_offset
        )


@dataclass(kw_only=True)
class Loop(AaaTreeNode):
    condition: "FunctionBody"
    body: "FunctionBody"

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Loop":
        assert tree.token_type == NonTerminal.LOOP

        condition = FunctionBody.from_tree(tree.children[1], tokens, code)
        loop_body = FunctionBody.from_tree(tree.children[3], tokens, code)
        return Loop(
            condition=condition,
            body=loop_body,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class Identifier(AaaTreeNode):
    name: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Identifier":
        name = tree.value(tokens, code)
        return Identifier(
            name=name, token_count=tree.token_count, token_offset=tree.token_offset
        )


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
            else_body = FunctionBody(
                items=[], token_count=tree.token_count, token_offset=tree.token_offset
            )

        return Branch(
            condition=condition,
            if_body=if_body,
            else_body=else_body,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class FunctionBody(AaaTreeNode):
    items: List[FunctionBodyItem]

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "FunctionBody":
        assert tree.token_type == NonTerminal.FUNCTION_BODY

        aaa_tree_nodes: Dict[Optional[IntEnum], Type[FunctionBodyItem]] = {
            NonTerminal.BOOLEAN: BooleanLiteral,
            NonTerminal.BRANCH: Branch,
            NonTerminal.LOOP: Loop,
            NonTerminal.OPERATOR: Operator,
            NonTerminal.TYPE_LITERAL: TypeLiteral,
            Terminal.IDENTIFIER: Identifier,
            Terminal.INTEGER: IntegerLiteral,
            Terminal.STRING: StringLiteral,
        }

        items: List[FunctionBodyItem] = []

        for child in tree.children:
            aaa_tree_node = aaa_tree_nodes[child.token_type]
            items.append(aaa_tree_node.from_tree(child, tokens, code))

        return FunctionBody(
            items=items, token_count=tree.token_count, token_offset=tree.token_offset
        )


@dataclass(kw_only=True)
class Argument(AaaTreeNode):
    name: str
    type: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Argument":
        assert tree.token_type == NonTerminal.ARGUMENT

        if tree[0].token_type in [Terminal.IDENTIFIER, NonTerminal.TYPE_LITERAL]:
            return Argument(
                name=tree[0].value(tokens, code),
                type=tree[2].value(tokens, code),
                token_count=tree.token_count,
                token_offset=tree.token_offset,
            )

        elif tree[0].token_type == Terminal.ASTERISK:
            return Argument(
                name=tree[1].value(tokens, code),
                type="*" + tree[1].value(tokens, code),
                token_count=tree.token_count,
                token_offset=tree.token_offset,
            )

        else:  # pragma: nocover
            assert False


@dataclass(kw_only=True)
class ReturnType(AaaTreeNode):
    type: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "ReturnType":
        assert tree.token_type == NonTerminal.RETURN_TYPE

        if tree[0].token_type in [Terminal.IDENTIFIER, NonTerminal.TYPE_LITERAL]:
            return ReturnType(
                type=tree[0].value(tokens, code),
                token_count=tree.token_count,
                token_offset=tree.token_offset,
            )

        elif tree[0].token_type == Terminal.ASTERISK:
            return ReturnType(
                type="*" + tree[1].value(tokens, code),
                token_count=tree.token_count,
                token_offset=tree.token_offset,
            )

        else:  # pragma: nocover
            assert False


@dataclass(kw_only=True)
class Function(AaaTreeNode):
    name: str
    arguments: List[Argument]
    return_types: List[ReturnType]
    body: FunctionBody

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
            name=name,
            arguments=arguments,
            return_types=return_types,
            body=body,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class ImportItem(AaaTreeNode):
    origninal_name: str
    imported_name: str

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "ImportItem":
        assert tree.token_type == NonTerminal.IMPORT_ITEM

        origninal_name = tree[0].value(tokens, code)

        if len(tree.children) == 3:
            imported_name = tree[2].value(tokens, code)
        else:
            imported_name = tree[0].value(tokens, code)

        return ImportItem(
            origninal_name=origninal_name,
            imported_name=imported_name,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class Import(AaaTreeNode):
    source: str
    imported_items: List[ImportItem]

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "Import":
        assert tree.token_type == NonTerminal.IMPORT_STATEMENT

        source = tree[1].value(tokens, code)[1:-1]
        imported_items = [
            ImportItem.from_tree(child, tokens, code)
            for child in tree[3].children
            if child.token_type == NonTerminal.IMPORT_ITEM
        ]

        return Import(
            source=source,
            imported_items=imported_items,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )


@dataclass(kw_only=True)
class ParsedFile(AaaTreeNode):
    functions: List[Function]
    imports: List[Import]

    @classmethod
    def from_tree(cls, tree: Tree, tokens: List[Token], code: str) -> "ParsedFile":
        assert tree.token_type == NonTerminal.ROOT
        assert tree.token_count == len(tokens)

        functions: List[Function] = []
        imports: List[Import] = []

        for child in tree.children:
            if child.token_type == NonTerminal.FUNCTION_DEFINITION:
                function = Function.from_tree(child, tokens, code)
                functions.append(function)

            elif child.token_type == NonTerminal.IMPORT_STATEMENT:
                import_ = Import.from_tree(child, tokens, code)
                imports.append(import_)

            else:  # pragma: nocover
                assert False

        return ParsedFile(
            functions=functions,
            imports=imports,
            token_count=tree.token_count,
            token_offset=tree.token_offset,
        )

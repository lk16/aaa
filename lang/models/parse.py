from __future__ import annotations

from typing import List, Union

from lark.lexer import Token

from lang.models import AaaModel


class AaaTreeNode(AaaModel):
    class Config:
        frozen = True


class FunctionBodyItem(AaaTreeNode):
    ...


class IntegerLiteral(FunctionBodyItem):
    value: int


class StringLiteral(FunctionBodyItem):
    value: str


class BooleanLiteral(FunctionBodyItem):
    value: bool


class TypeLiteral(FunctionBodyItem):
    type_name: str
    type_parameters: List[ParsedType]


class Operator(FunctionBodyItem):
    value: str


class Loop(FunctionBodyItem):
    condition: FunctionBody
    body: FunctionBody


class LoopCondition(AaaTreeNode):
    value: FunctionBody


class LoopBody(AaaTreeNode):
    value: FunctionBody


class Identifier(FunctionBodyItem):
    token: Token
    name: str


class Branch(FunctionBodyItem):
    condition: FunctionBody
    if_body: FunctionBody
    else_body: FunctionBody


class BranchCondition(AaaTreeNode):
    value: FunctionBody


class BranchIfBody(AaaTreeNode):
    value: FunctionBody


class BranchElseBody(AaaTreeNode):
    value: FunctionBody


class MemberFunctionName(FunctionBodyItem):
    type_name: str
    func_name: str

    def __str__(self) -> str:
        return f"{self.type_name}:{self.func_name}"


class StructFieldQuery(FunctionBodyItem):
    operator_token: Token
    field_name: StringLiteral


class StructFieldUpdate(FunctionBodyItem):
    operator_token: Token
    field_name: StringLiteral
    new_value_expr: FunctionBody


class FunctionBody(AaaTreeNode):
    items: List[FunctionBodyItem]


class ParsedTypePlaceholder(AaaTreeNode):
    name: str


class ParsedType(AaaTreeNode):
    type: Union[TypeLiteral, ParsedTypePlaceholder]  # TODO use inheritance instead


class Argument(AaaTreeNode):
    name_token: Token
    name: str
    type: ParsedType


class Function(AaaTreeNode):
    token: Token
    name: str | MemberFunctionName
    arguments: List[Argument]
    return_types: List[ParsedType]
    body: FunctionBody

    def identify(self) -> str:
        if isinstance(self.name, str):
            return self.name
        elif isinstance(self.name, MemberFunctionName):
            return f"{self.name.type_name}:{self.name.func_name}"
        else:  # pragma: nocover
            assert False


class ImportItem(AaaTreeNode):
    origninal_name: str
    imported_name: str


class Import(AaaTreeNode):
    token: Token
    source: str
    imported_items: List[ImportItem]


class Struct(AaaTreeNode):
    token: Token
    name: str
    fields: List[Argument]

    def identify(self) -> str:
        return self.name


class BuiltinFunction(AaaTreeNode):
    name: str
    arguments: List[ParsedType]
    return_types: List[ParsedType]


class BuiltinFunctionArguments(AaaTreeNode):
    value: List[ParsedType]


class BuiltinFunctionReturnTypes(AaaTreeNode):
    value: List[ParsedType]


class ParsedBuiltinsFile(AaaTreeNode):
    functions: List[BuiltinFunction]


class ParsedFile(AaaTreeNode):
    functions: List[Function]
    imports: List[Import]
    structs: List[Struct]


LoopBody.update_forward_refs()
LoopCondition.update_forward_refs()
Loop.update_forward_refs()
Branch.update_forward_refs()
BranchCondition.update_forward_refs()
BranchIfBody.update_forward_refs()
BranchElseBody.update_forward_refs()
TypeLiteral.update_forward_refs()
StructFieldUpdate.update_forward_refs()
StructFieldQuery.update_forward_refs()

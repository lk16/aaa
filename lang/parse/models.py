from __future__ import annotations

from pathlib import Path
from typing import List, Union

from pydantic import BaseModel


class AaaModel(BaseModel):
    class Config:
        extra = "forbid"
        frozen = True


class AaaTreeNode(AaaModel):
    class Config:
        extra = "forbid"
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


class MemberFunction(FunctionBodyItem):
    type_name: str
    func_name: str


class StructFieldQuery(FunctionBodyItem):
    field_name: StringLiteral


class StructFieldUpdate(FunctionBodyItem):
    field_name: StringLiteral
    new_value_expr: FunctionBody


class FunctionBody(AaaTreeNode):
    items: List[FunctionBodyItem]


class ParsedTypePlaceholder(AaaTreeNode):
    name: str


class ParsedType(AaaTreeNode):
    type: Union[TypeLiteral, ParsedTypePlaceholder]


class Argument(AaaTreeNode):
    name: str
    type: ParsedType


class Function(AaaTreeNode):
    name: str | MemberFunction
    arguments: List[Argument]
    return_types: List[ParsedType]
    body: FunctionBody

    def name_key(self) -> str:
        if isinstance(self.name, str):
            return self.name
        elif isinstance(self.name, MemberFunction):
            return f"{self.name.type_name}:{self.name.func_name}"
        else:  # pragma: nocover
            assert False


class ImportItem(AaaTreeNode):
    origninal_name: str
    imported_name: str


class Import(AaaTreeNode):
    source: str
    imported_items: List[ImportItem]


class Struct(AaaTreeNode):
    name: str
    fields: List[Argument]


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


# TODO this is not created by parser/transformer, move out of parse module
class ProgramImport(AaaModel):
    original_name: str
    source_file: Path


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
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from lang.models import AaaModel
from lang.parser import models as parser


class AaaCrossReferenceModel(AaaModel):
    ...


class Unresolved(AaaCrossReferenceModel):
    ...


class Struct(AaaCrossReferenceModel):
    # TODO use Type for Struct as well

    parsed: parser.Struct
    fields: Dict[str, Type | Struct | Unresolved]
    name: str

    def identify(self) -> str:
        return self.name


class Function(AaaCrossReferenceModel):
    parsed: parser.Function
    name: str
    type_name: str
    arguments: Dict[str, VariableType | Unresolved]
    body: FunctionBody | Unresolved

    def identify(self) -> str:
        if self.type_name:
            return f"{self.type_name}:{self.name}"
        return self.name


class FunctionBody(AaaCrossReferenceModel):
    items: List[FunctionBodyItem]


class Import(AaaCrossReferenceModel):
    parsed: parser.ImportItem
    source_file: Path
    source_name: str
    imported_name: str
    source: Unresolved | Struct | Function  # TODO consider using Identifiable here

    def identify(self) -> str:
        return self.imported_name


class Type(AaaCrossReferenceModel):
    parsed: parser.TypeLiteral
    name: str
    param_count: int

    def identify(self) -> str:
        return self.name


class TypePlaceholder(AaaCrossReferenceModel):
    parsed: parser.TypePlaceholder
    function: Function
    name: str

    def identify(self) -> str:
        return self.function.identify() + f":{self.name}"


class VariableType(AaaCrossReferenceModel):
    parsed: parser.TypeLiteral | parser.TypePlaceholder
    type: Type | TypePlaceholder
    name: str
    params: List[VariableType]
    is_placeholder: bool


class FunctionBodyItem(AaaCrossReferenceModel):
    ...


class IntegerLiteral(FunctionBodyItem, parser.IntegerLiteral):
    ...


class StringLiteral(FunctionBodyItem, parser.StringLiteral):
    ...


class BooleanLiteral(FunctionBodyItem, parser.BooleanLiteral):
    ...


class Operator(FunctionBodyItem, parser.Operator):
    ...


class Loop(FunctionBodyItem, parser.Loop):
    ...


class IdentifierKind(AaaCrossReferenceModel):
    ...


class IdentifierUsingArgument(IdentifierKind):
    arg_type: VariableType


class IdentifierCallingFunction(IdentifierKind):
    function: Function


class Identifier(FunctionBodyItem, parser.Identifier):
    kind: IdentifierKind


class Branch(FunctionBodyItem, parser.Branch):
    ...


class MemberFunctionName(FunctionBodyItem, parser.MemberFunctionName):
    ...


class StructFieldQuery(FunctionBodyItem, parser.StructFieldQuery):
    ...


class StructFieldUpdate(FunctionBodyItem, parser.StructFieldUpdate):
    ...


Function.update_forward_refs()
Struct.update_forward_refs()
FunctionBody.update_forward_refs()

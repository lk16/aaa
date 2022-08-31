from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from lark.lexer import Token

from lang.models import AaaModel
from lang.parser.exceptions import ParseException


class AaaParseModel(AaaModel):
    token: Token


class FunctionBodyItem(AaaParseModel):
    ...


class IntegerLiteral(FunctionBodyItem):
    value: int


class StringLiteral(FunctionBodyItem):
    value: str


class BooleanLiteral(FunctionBodyItem):
    value: bool


class Operator(FunctionBodyItem):
    value: str


class Loop(FunctionBodyItem):
    condition: FunctionBody
    body: FunctionBody


class LoopCondition(AaaParseModel):
    value: FunctionBody


class LoopBody(AaaParseModel):
    value: FunctionBody


class Identifier(FunctionBodyItem):
    name: str


class Branch(FunctionBodyItem):
    condition: FunctionBody
    if_body: FunctionBody
    else_body: FunctionBody


class FunctionBody(AaaParseModel):
    items: List[FunctionBodyItem]


class BranchCondition(FunctionBody):
    ...


class BranchIfBody(FunctionBody):
    ...


class BranchElseBody(FunctionBody):
    ...


class MemberFunctionLiteral(FunctionBodyItem):
    struct_name: TypeLiteral
    func_name: Identifier


class StructFieldQuery(FunctionBodyItem):
    field_name: StringLiteral


class StructFieldUpdate(FunctionBodyItem):
    field_name: StringLiteral
    new_value_expr: FunctionBody


class Argument(AaaParseModel):
    identifier: Identifier
    type: TypeLiteral


class Function(AaaParseModel):
    name: MemberFunctionLiteral | Identifier
    type_params: List[TypeLiteral]
    arguments: Dict[str, Argument]
    return_types: List[TypeLiteral]
    body: FunctionBody


class ImportItem(AaaParseModel):
    origninal_name: str
    imported_name: str


class Import(AaaParseModel):
    source: str
    imported_items: List[ImportItem]


class Struct(AaaParseModel):
    identifier: Identifier
    fields: Dict[str, TypeLiteral]


class ParsedFile(AaaParseModel):
    functions: List[Function]
    imports: List[Import]
    structs: List[Struct]
    types: List[TypeLiteral]


class TypeLiteral(AaaParseModel):
    identifier: Identifier
    params: TypeParameters


class TypeParameters(AaaParseModel):
    value: List[TypeLiteral]


LoopBody.update_forward_refs()
LoopCondition.update_forward_refs()
Loop.update_forward_refs()
Branch.update_forward_refs()
BranchCondition.update_forward_refs()
BranchIfBody.update_forward_refs()
BranchElseBody.update_forward_refs()
StructFieldUpdate.update_forward_refs()
StructFieldQuery.update_forward_refs()
Argument.update_forward_refs()
Function.update_forward_refs()
TypeLiteral.update_forward_refs()
Struct.update_forward_refs()
ParsedFile.update_forward_refs()
MemberFunctionLiteral.update_forward_refs()


class ParserOutput(AaaModel):
    parsed: Dict[Path, ParsedFile]
    builtins_path: Path
    exceptions: List[ParseException]

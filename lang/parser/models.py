from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from lark.lexer import Token

from lang.models import AaaModel
from lang.parser.exceptions import ParseException


class AaaParseModel(AaaModel):
    ...


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
    token: Token
    name: str


class Branch(FunctionBodyItem):
    condition: FunctionBody
    if_body: FunctionBody
    else_body: FunctionBody


class BranchCondition(AaaParseModel):
    value: FunctionBody


class BranchIfBody(AaaParseModel):
    value: FunctionBody


class BranchElseBody(AaaParseModel):
    value: FunctionBody


class MemberFunctionName(FunctionBodyItem):
    type_name: str
    func_name: str


class StructFieldQuery(FunctionBodyItem):
    operator_token: Token
    field_name: StringLiteral


class StructFieldUpdate(FunctionBodyItem):
    operator_token: Token
    field_name: StringLiteral
    new_value_expr: FunctionBody


class FunctionBody(AaaParseModel):
    items: List[FunctionBodyItem]


class Argument(AaaParseModel):
    name_token: Token
    name: str
    type: TypeLiteral | TypePlaceholder


class Function(AaaParseModel):
    token: Token
    name: str | MemberFunctionName
    arguments: List[Argument]
    return_types: List[TypeLiteral | TypePlaceholder]
    body: FunctionBody

    # TODO create fields name and type_name instead of doing this
    def get_name(self) -> str:
        if isinstance(self.name, MemberFunctionName):
            return self.name.func_name
        return self.name

    def get_type_name(self) -> str:
        if isinstance(self.name, MemberFunctionName):
            return self.name.type_name
        return ""


class ImportItem(AaaParseModel):
    origninal_name: str
    imported_name: str


class Import(AaaParseModel):
    token: Token
    source: str
    imported_items: List[ImportItem]


class Struct(AaaParseModel):
    token: Token
    name: str
    fields: List[Tuple[str, TypeLiteral | TypePlaceholder]]


class ParsedFile(AaaParseModel):
    functions: List[Function]
    imports: List[Import]
    structs: List[Struct]
    types: List[TypeLiteral]


class TypeLiteral(AaaParseModel):
    name: str
    token: Token
    params: List[TypeLiteral | TypePlaceholder]


class TypeParams(AaaParseModel):
    ...


class TypePlaceholder(AaaParseModel):
    name: str
    token: Token


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


class ParserOutput(AaaModel):
    parsed: Dict[Path, ParsedFile]
    builtins_path: Path
    exceptions: List[ParseException]

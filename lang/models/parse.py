from __future__ import annotations

from typing import Dict, List, Optional

from lark.lexer import Token

from lang.models import AaaTreeNode, FunctionBodyItem
from lang.models.typing.var_type import VariableType


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


class Argument(AaaTreeNode):
    name_token: Token
    name: str
    type: VariableType


class Function(AaaTreeNode):
    token: Token
    name: str | MemberFunctionName
    arguments: List[Argument]
    return_types: List[VariableType]
    body: FunctionBody

    def identify(self) -> str:
        if isinstance(self.name, str):
            return self.name
        elif isinstance(self.name, MemberFunctionName):
            return f"{self.name.type_name}:{self.name.func_name}"
        else:  # pragma: nocover
            assert False

    def get_arg_type(self, name: str) -> Optional[VariableType]:
        for argument in self.arguments:
            if (argument.type.is_placeholder() and argument.type.name == name) or (
                not argument.type.is_placeholder() and argument.name == name
            ):
                return argument.type

        return None


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
    fields: Dict[str, VariableType]

    def identify(self) -> str:
        return self.name


# TODO make builtin functions just a regular Function
class BuiltinFunction(AaaTreeNode):
    name: str
    arguments: List[VariableType]
    return_types: List[VariableType]

    def identify(self) -> str:
        return self.name


class BuiltinFunctionArguments(AaaTreeNode):
    value: List[VariableType]


class BuiltinFunctionReturnTypes(AaaTreeNode):
    value: List[VariableType]


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
StructFieldUpdate.update_forward_refs()
StructFieldQuery.update_forward_refs()

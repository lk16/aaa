from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

FunctionBodyItem = Union[
    "BooleanLiteral",
    "Branch",
    "Identifier",
    "IntegerLiteral",
    "Loop",
    "MemberFunction",
    "Operator",
    "StringLiteral",
    "StructFieldQuery",
    "StructFieldUpdate",
    "TypeLiteral",
]


@dataclass(kw_only=True, frozen=True)
class AaaTreeNode:
    ...


@dataclass(kw_only=True, frozen=True)
class IntegerLiteral(AaaTreeNode):
    value: int


@dataclass(kw_only=True, frozen=True)
class StringLiteral(AaaTreeNode):
    value: str


@dataclass(kw_only=True, frozen=True)
class BooleanLiteral(AaaTreeNode):
    value: bool


@dataclass(kw_only=True, frozen=True)
class TypeLiteral(AaaTreeNode):
    type_name: str
    type_parameters: List[ParsedType]


@dataclass(kw_only=True, frozen=True)
class Operator(AaaTreeNode):
    value: str


@dataclass(kw_only=True, frozen=True)
class Loop(AaaTreeNode):
    condition: "FunctionBody"
    body: "FunctionBody"


@dataclass(kw_only=True, frozen=True)
class LoopCondition(AaaTreeNode):
    value: "FunctionBody"


@dataclass(kw_only=True, frozen=True)
class LoopBody(AaaTreeNode):
    value: "FunctionBody"


@dataclass(kw_only=True, frozen=True)
class Identifier(AaaTreeNode):
    name: str


@dataclass(kw_only=True, frozen=True)
class Branch(AaaTreeNode):
    condition: "FunctionBody"
    if_body: "FunctionBody"
    else_body: "FunctionBody"


@dataclass(kw_only=True, frozen=True)
class BranchCondition(AaaTreeNode):
    value: "FunctionBody"


@dataclass(kw_only=True, frozen=True)
class BranchIfBody(AaaTreeNode):
    value: "FunctionBody"


@dataclass(kw_only=True, frozen=True)
class BranchElseBody(AaaTreeNode):
    value: "FunctionBody"


@dataclass(kw_only=True, frozen=True)
class MemberFunction(AaaTreeNode):
    type_name: str
    func_name: str


@dataclass(kw_only=True, frozen=True)
class StructFieldQuery(AaaTreeNode):
    field_name: StringLiteral


@dataclass(kw_only=True, frozen=True)
class StructFieldUpdate(AaaTreeNode):
    field_name: StringLiteral
    new_value_expr: FunctionBody


@dataclass(kw_only=True, frozen=True)
class FunctionBody(AaaTreeNode):
    items: List[FunctionBodyItem]


@dataclass(kw_only=True, frozen=True)
class ParsedTypePlaceholder(AaaTreeNode):
    name: str


@dataclass(kw_only=True, frozen=True)
class ParsedType(AaaTreeNode):
    type: Union[TypeLiteral, ParsedTypePlaceholder]


@dataclass(kw_only=True, frozen=True)
class Argument(AaaTreeNode):
    name: str
    type: ParsedType


@dataclass(kw_only=True, frozen=True)
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


@dataclass(kw_only=True, frozen=True)
class ImportItem(AaaTreeNode):
    origninal_name: str
    imported_name: str


@dataclass(kw_only=True, frozen=True)
class Import(AaaTreeNode):
    source: str
    imported_items: List[ImportItem]


@dataclass(kw_only=True, frozen=True)
class Struct(AaaTreeNode):
    name: str
    fields: List[Argument]


@dataclass(kw_only=True, frozen=True)
class BuiltinFunction(AaaTreeNode):
    name: str
    arguments: List[ParsedType]
    return_types: List[ParsedType]


@dataclass(kw_only=True, frozen=True)
class BuiltinFunctionArguments(AaaTreeNode):
    value: List[ParsedType]


@dataclass(kw_only=True, frozen=True)
class BuiltinFunctionReturnTypes(AaaTreeNode):
    value: List[ParsedType]


@dataclass(kw_only=True, frozen=True)
class ParsedBuiltinsFile(AaaTreeNode):
    functions: List[BuiltinFunction]


@dataclass(kw_only=True, frozen=True)
class ParsedFile(AaaTreeNode):
    functions: List[Function]
    imports: List[Import]
    structs: List[Struct]

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Sequence, Tuple, Union

from aaa import AaaModel

if TYPE_CHECKING:
    from aaa.cross_referencer.exceptions import CrossReferenceBaseException

from aaa.parser import models as parser

Identifiable = Union["Function", "Import", "Struct", "Type"]

IdentifiablesDict = Dict[Tuple[Path, str], Identifiable]


class AaaCrossReferenceModel(AaaModel):
    ...


class Unresolved(AaaCrossReferenceModel):
    ...


class Struct(AaaCrossReferenceModel):
    # TODO use Type for Struct as well

    def __init__(
        self,
        *,
        parsed: parser.Struct,
        fields: Dict[str, Identifiable | Unresolved],
        name: str,
    ) -> None:
        self.parsed = parsed
        self.fields = fields
        self.name = name

    def identify(self) -> str:
        return self.name


class Function(AaaCrossReferenceModel):
    def __init__(
        self,
        *,
        parsed: parser.Function,
        name: str,
        type_params: Dict[str, Type | Unresolved],
        struct_name: str,
        arguments: Dict[str, VariableType | Unresolved],
        body: FunctionBody | Unresolved,
    ) -> None:
        self.parsed = parsed
        self.name = name
        self.type_params = type_params
        self.struct_name = struct_name
        self.arguments = arguments
        self.body = body

    def identify(self) -> str:
        if self.struct_name:
            return f"{self.struct_name}:{self.name}"
        return self.name


class FunctionBodyItem(AaaCrossReferenceModel, parser.FunctionBodyItem):
    ...


class FunctionBody(FunctionBodyItem, parser.FunctionBody):
    def __init__(self, *, items: Sequence[FunctionBodyItem]) -> None:
        self.items = items


class Import(AaaCrossReferenceModel):
    def __init__(
        self,
        *,
        parsed: parser.ImportItem,
        source_file: Path,
        source_name: str,
        imported_name: str,
        source: Identifiable | Unresolved,
    ) -> None:
        self.parsed = parsed
        self.source_file = source_file
        self.source_name = source_name
        self.imported_name = imported_name
        self.source = source

    def identify(self) -> str:
        return self.imported_name


class Type(AaaCrossReferenceModel):
    def __init__(
        self,
        *,
        parsed: parser.TypeLiteral,
        name: str,
        param_count: int,
    ) -> None:
        self.parsed = parsed
        self.name = name
        self.param_count = param_count

    def identify(self) -> str:
        return self.name


class VariableType(AaaCrossReferenceModel):
    def __init__(
        self,
        *,
        parsed: parser.TypeLiteral,
        type: Type,
        name: str,
        params: List[VariableType],
        is_placeholder: bool,
    ) -> None:
        self.parsed = parsed
        self.type = type
        self.name = name
        self.params = params
        self.is_placeholder = is_placeholder


class IntegerLiteral(FunctionBodyItem, parser.IntegerLiteral):
    def __init__(self, *, parsed: parser.IntegerLiteral) -> None:
        super().__init__(**vars(parsed))


class StringLiteral(FunctionBodyItem, parser.StringLiteral):
    def __init__(self, *, parsed: parser.StringLiteral) -> None:
        super().__init__(**vars(parsed))


class BooleanLiteral(FunctionBodyItem, parser.BooleanLiteral):
    def __init__(self, *, parsed: parser.BooleanLiteral) -> None:
        super().__init__(**vars(parsed))


class Operator(FunctionBodyItem, parser.Operator):
    def __init__(self, *, parsed: parser.Operator) -> None:
        super().__init__(**vars(parsed))


class Loop(FunctionBodyItem, parser.Loop):
    def __init__(
        self, *, condition: FunctionBody, body: FunctionBody, parsed: parser.Loop
    ) -> None:
        self.condition = condition
        self.body = body
        super().__init__(**vars(parsed))


class IdentifierKind(AaaCrossReferenceModel):
    ...


class IdentifierUsingArgument(IdentifierKind):
    def __init__(self, *, arg_type: VariableType) -> None:
        self.arg_type = arg_type


class IdentifierCallingFunction(IdentifierKind):
    def __init__(self, *function: Function) -> None:
        self.function = function


class Identifier(FunctionBodyItem, parser.Identifier):
    def __init__(self, *, kind: IdentifierKind, parsed: parser.Identifier) -> None:
        self.kind = kind
        super().__init__(**vars(parsed))


class Branch(FunctionBodyItem, parser.Branch):
    def __init__(
        self,
        *,
        condition: FunctionBody,
        if_body: FunctionBody,
        else_body: FunctionBody,
        parsed: parser.Branch,
    ) -> None:
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body
        super().__init__(**vars(parsed))


class MemberFunctionName(FunctionBodyItem, parser.MemberFunctionLiteral):
    def __init__(self, *, parsed: parser.MemberFunctionLiteral) -> None:
        super().__init__(**vars(parsed))


class StructFieldQuery(FunctionBodyItem, parser.StructFieldQuery):
    def __init__(self, *, parsed: parser.StructFieldQuery) -> None:
        super().__init__(**vars(parsed))


class StructFieldUpdate(FunctionBodyItem, parser.StructFieldUpdate):
    def __init__(self, *, parsed: parser.StructFieldUpdate) -> None:
        super().__init__(**vars(parsed))


class CrossReferencerOutput(AaaModel):
    def __init__(
        self,
        *,
        identifiers: IdentifiablesDict,
        exceptions: List[CrossReferenceBaseException],
    ) -> None:
        self.identifiers = identifiers
        self.exceptions = exceptions

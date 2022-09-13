from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence, Tuple

from aaa import AaaModel

if TYPE_CHECKING:
    from aaa.cross_referencer.exceptions import CrossReferenceBaseException

from aaa.parser import models as parser


class AaaCrossReferenceModel(AaaModel):
    ...


class Unresolved(AaaCrossReferenceModel):
    ...


class Identifiable(AaaCrossReferenceModel):
    def __init__(self) -> None:
        self.parsed: parser.AaaParseModel

    def identify(self) -> Tuple[Path, str]:
        return (self.file(), self.name())

    def file(self) -> Path:
        raise NotImplementedError

    def name(self) -> str:
        raise NotImplementedError


IdentifiablesDict = Dict[Tuple[Path, str], Identifiable]


class Function(Identifiable):
    def __init__(
        self,
        *,
        parsed: parser.Function,
        type_params: Dict[str, Type] | Unresolved,
        arguments: List[Argument] | Unresolved,
        return_types: List[VariableType] | Unresolved,
        body: FunctionBody | Unresolved,
    ) -> None:
        self.parsed: parser.Function = parsed
        self.type_params = type_params
        self.arguments = arguments
        self.return_types = return_types
        self.body = body

    def get_argument(self, name: str) -> Optional[Argument]:
        assert not isinstance(self.arguments, Unresolved)

        for argument in self.arguments:
            if name == argument.name:
                return argument
        return None

    def name(self) -> str:
        struct_name, func_name = self.parsed.get_names()

        if struct_name:
            return f"{struct_name}:{func_name}"
        return func_name

    def file(self) -> Path:
        return self.parsed.file

    def is_member_function(self) -> bool:
        struct_name, _ = self.parsed.get_names()
        return struct_name != ""


class Argument(AaaCrossReferenceModel):
    def __init__(self, *, type: VariableType, name: str, file: Path) -> None:
        self.type = type
        self.name = name
        self.file = file


class FunctionBodyItem(AaaCrossReferenceModel, parser.FunctionBodyItem):
    ...


class FunctionBody(FunctionBodyItem, parser.FunctionBody):
    def __init__(self, *, items: Sequence[FunctionBodyItem], file: Path) -> None:
        self.items = items
        self.file = file


class Import(Identifiable):
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

    def name(self) -> str:
        return self.imported_name

    def file(self) -> Path:
        return self.parsed.file


class Type(Identifiable):
    def __init__(
        self,
        *,
        parsed: parser.TypeLiteral | parser.Struct,
        param_count: int,
        fields: Dict[str, VariableType] | Unresolved,
    ) -> None:
        self.parsed: parser.TypeLiteral | parser.Struct = parsed
        self.param_count = param_count
        self.fields = fields

    def name(self) -> str:
        return self.parsed.identifier.name

    def file(self) -> Path:
        return self.parsed.file


class VariableType(AaaCrossReferenceModel):
    def __init__(
        self,
        *,
        parsed: parser.TypeLiteral,
        type: Type,
        params: List[VariableType],
        is_placeholder: bool,
    ) -> None:
        self.parsed = parsed
        self.type = type
        self.params = params
        self.is_placeholder = is_placeholder

    def name(self) -> str:
        return self.type.name()

    def file(self) -> Path:
        return self.type.file()

    def __repr__(self) -> str:
        output = self.name()

        if self.params:
            output += "["
            for param in self.params:
                output += repr(param)
            output += "]"

        return output


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
        self,
        *,
        condition: FunctionBody,
        body: FunctionBody,
        parsed: parser.Loop,
    ) -> None:
        self.condition: FunctionBody = condition
        self.body: FunctionBody = body
        super().__init__(**vars(parsed))


class IdentifierKind(AaaCrossReferenceModel):
    ...


class IdentifierUsingArgument(IdentifierKind):
    def __init__(self, *, arg_type: VariableType) -> None:
        self.arg_type = arg_type


class IdentifierCallingFunction(IdentifierKind):
    def __init__(self, *, function: Function) -> None:
        self.function = function


class IdentifierCallingType(IdentifierKind):
    def __init__(self, *, type: Type) -> None:
        self.type = type


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
        self.condition: FunctionBody = condition
        self.if_body: FunctionBody = if_body
        self.else_body: FunctionBody = else_body
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
        self.new_value_expr: FunctionBody


class CrossReferencerOutput(AaaModel):
    def __init__(
        self,
        *,
        identifiers: IdentifiablesDict,
        builtins_path: Path,
        exceptions: List[CrossReferenceBaseException],
    ) -> None:
        self.identifiers = identifiers
        self.exceptions = exceptions
        self.builtins_path = builtins_path

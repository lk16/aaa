from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from aaa import AaaModel, Position
from aaa.parser import models as parser


class AaaCrossReferenceModel(AaaModel):
    def __init__(self, position: Position) -> None:
        self.position = position


class Identifiable(AaaCrossReferenceModel):
    def __init__(self, position: Position, name: str) -> None:
        self.name = name
        super().__init__(position)

    def identify(self) -> Tuple[Path, str]:
        return (self.position.file, self.name)


IdentifiablesDict = Dict[Tuple[Path, str], Identifiable]


class UnresolvedFunction(AaaCrossReferenceModel):
    def __init__(self, parsed: parser.Function) -> None:
        self.parsed = parsed
        self.func_name = parsed.func_name.name

        if parsed.struct_name:
            self.struct_name = parsed.struct_name.name
        else:
            self.struct_name = ""

        if parsed.struct_name:
            name = f"{self.struct_name}:{self.func_name}"
        else:
            name = self.func_name

        self.name = name
        super().__init__(parsed.position)


class Function(Identifiable):
    def __init__(
        self,
        unresolved: UnresolvedFunction,
        type_params: Dict[str, Type],
        arguments: List[Argument],
        return_types: List[VariableType],
    ) -> None:
        self.type_params = type_params
        self.arguments = arguments
        self.return_types = return_types
        self.body: Optional[FunctionBody] = None

        self.func_name = unresolved.func_name
        self.struct_name = unresolved.struct_name
        super().__init__(unresolved.position, unresolved.name)

    def get_argument(self, name: str) -> Optional[Argument]:
        for argument in self.arguments:
            if name == argument.name:
                return argument
        return None

    def is_member_function(self) -> bool:
        return self.struct_name != ""


class Argument(AaaCrossReferenceModel):
    def __init__(self, var_type: VariableType, name: str) -> None:
        self.var_type = var_type
        self.name = name
        super().__init__(var_type.position)


class FunctionBodyItem(AaaCrossReferenceModel):
    ...


class FunctionBody(FunctionBodyItem):
    def __init__(
        self, parsed: parser.FunctionBody, items: List[FunctionBodyItem]
    ) -> None:
        self.items = items
        super().__init__(parsed.position)


class UnresolvedImport(AaaCrossReferenceModel):
    def __init__(self, import_item: parser.ImportItem, import_: parser.Import) -> None:
        self.source_file = import_.source_file
        self.source_name = import_item.original_name
        self.name = import_item.imported_name
        super().__init__(import_item.position)


class Import(Identifiable):
    def __init__(self, unresolved: UnresolvedImport, source: Identifiable) -> None:
        self.source_file = unresolved.source_file
        self.source_name = unresolved.source_name
        self.source = source
        super().__init__(unresolved.position, unresolved.name)


class UnresolvedType(AaaCrossReferenceModel):
    def __init__(
        self,
        parsed: parser.TypeLiteral | parser.Struct,
        param_count: int,
    ) -> None:
        self.param_count = param_count
        self.parsed_field_types: Dict[str, parser.TypeLiteral] = {}

        if isinstance(parsed, parser.Struct):
            self.parsed_field_types = parsed.fields

        self.name = parsed.identifier.name
        super().__init__(parsed.position)


class Type(Identifiable):
    def __init__(
        self, unresolved: UnresolvedType, fields: Dict[str, VariableType]
    ) -> None:
        self.param_count = unresolved.param_count
        self.fields = fields
        super().__init__(unresolved.position, unresolved.name)


class VariableType(AaaCrossReferenceModel):
    def __init__(
        self,
        parsed: parser.TypeLiteral,
        type: Type,
        params: List[VariableType],
        is_placeholder: bool,
    ) -> None:
        self.type = type
        self.params = params
        self.is_placeholder = is_placeholder
        self.name = self.type.name
        super().__init__(parsed.position)

    def __repr__(self) -> str:
        output = self.name

        if self.params:
            output += "["
            output += ", ".join(repr(param) for param in self.params)
            output += "]"

        return output

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VariableType):
            return False

        # NOTE: Type instances are unique, we can use identity here
        if self.type is not other.type:
            return False

        return self.params == other.params


class IntegerLiteral(FunctionBodyItem):
    def __init__(self, parsed: parser.IntegerLiteral) -> None:
        self.value = parsed.value
        super().__init__(parsed.position)


class StringLiteral(FunctionBodyItem, parser.StringLiteral):
    def __init__(self, parsed: parser.StringLiteral) -> None:
        self.value = parsed.value
        super().__init__(parsed.position)


class BooleanLiteral(FunctionBodyItem, parser.BooleanLiteral):
    def __init__(self, parsed: parser.BooleanLiteral) -> None:
        self.value = parsed.value
        super().__init__(parsed.position)


class Loop(FunctionBodyItem):
    def __init__(
        self,
        condition: FunctionBody,
        body: FunctionBody,
        parsed: parser.Loop,
    ) -> None:
        self.condition = condition
        self.body = body
        super().__init__(parsed.position)


class IdentifierKind(AaaModel):
    ...


class IdentifierUsingArgument(IdentifierKind):
    def __init__(self, arg_type: VariableType) -> None:
        self.arg_type = arg_type


class IdentifierCallingFunction(IdentifierKind):
    def __init__(self, function: Function) -> None:
        self.function = function


class IdentifierCallingType(IdentifierKind):
    def __init__(self, var_type: VariableType) -> None:
        self.var_type = var_type


class Identifier(FunctionBodyItem):
    def __init__(
        self,
        kind: IdentifierKind,
        type_params: List[Identifier],
        parsed: parser.Identifier,
    ) -> None:
        self.kind = kind
        self.name = parsed.name
        self.type_params = type_params
        super().__init__(parsed.position)


class Branch(FunctionBodyItem):
    def __init__(
        self,
        condition: FunctionBody,
        if_body: FunctionBody,
        else_body: Optional[FunctionBody],
        parsed: parser.Branch,
    ) -> None:
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body
        super().__init__(parsed.position)


class StructFieldQuery(FunctionBodyItem):
    def __init__(self, parsed: parser.StructFieldQuery) -> None:
        self.field_name = parsed.field_name
        super().__init__(parsed.position)


class StructFieldUpdate(FunctionBodyItem):
    def __init__(
        self, parsed: parser.StructFieldUpdate, new_value_expr: FunctionBody
    ) -> None:
        self.field_name = parsed.field_name
        self.new_value_expr = new_value_expr
        super().__init__(parsed.position)


class ArgumentIdentifiable(Identifiable):
    # NOTE: used for argument name collision with CollidingIdentifier
    ...


class CrossReferencerOutput(AaaModel):
    def __init__(
        self,
        types: Dict[Tuple[Path, str], Type],
        functions: Dict[Tuple[Path, str], Function],
        imports: Dict[Tuple[Path, str], Import],
        builtins_path: Path,
        entrypoint: Path,
    ) -> None:
        self.types = types
        self.functions = functions
        self.imports = imports
        self.builtins_path = builtins_path
        self.entrypoint = entrypoint

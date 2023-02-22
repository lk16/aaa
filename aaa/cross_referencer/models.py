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
        return_types: List[VariableType] | Never,
        is_enum_ctor: bool,
    ) -> None:
        self.type_params = type_params
        self.arguments = arguments
        self.return_types = return_types
        self.body: Optional[FunctionBody] = None
        self.is_enum_ctor = is_enum_ctor

        self.func_name = unresolved.func_name
        self.struct_name = unresolved.struct_name
        super().__init__(unresolved.position, unresolved.name)

    def is_member_function(self) -> bool:
        return self.struct_name != ""

    def is_test(self) -> bool:
        return (
            not self.is_member_function()
            and self.func_name.startswith("test_")
            and self.position.file.name.startswith("test_")
        )


class Argument(AaaCrossReferenceModel):
    def __init__(self, var_type: VariableType, identifier: parser.Identifier) -> None:
        self.var_type = var_type
        self.name = identifier.name
        super().__init__(identifier.position)


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
        self.source_name = import_item.original.name
        self.name = import_item.imported.name
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
        parsed: parser.TypeLiteral | parser.Struct | parser.Enum,
        param_count: int,
    ) -> None:
        self.param_count = param_count
        self.parsed_field_types: Dict[str, parser.TypeLiteral] = {}
        self.parsed_variants: Dict[str, Tuple[parser.TypeLiteral, int]] = {}

        if isinstance(parsed, parser.Struct):
            self.parsed_field_types = parsed.fields

        if isinstance(parsed, parser.Enum):
            for i, item in enumerate(parsed.variants):
                self.parsed_variants[item.name.name] = (item.type, i)

        self.name = parsed.identifier.name
        super().__init__(parsed.position)


class Type(Identifiable):
    def __init__(
        self,
        unresolved: UnresolvedType,
        fields: Dict[str, VariableType],
        enum_fields: Dict[str, Tuple[VariableType, int]],
    ) -> None:
        self.param_count = unresolved.param_count
        self.fields = fields
        self.enum_fields = enum_fields
        super().__init__(unresolved.position, unresolved.name)


class VariableType(AaaCrossReferenceModel):
    def __init__(
        self,
        type: Type,
        params: List[VariableType],
        is_placeholder: bool,
        position: Position,
        is_const: bool,
    ) -> None:
        self.type = type
        self.params = params
        self.is_placeholder = is_placeholder
        self.name = self.type.name
        self.is_const = is_const
        super().__init__(position)

    def __repr__(self) -> str:  # pragma: nocover
        output = self.name

        if self.params:
            output += "["
            output += ", ".join(repr(param) for param in self.params)
            output += "]"

        if self.is_const:
            return f"(const {output})"

        return output

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VariableType):  # pragma: nocover
            return False

        return (
            # NOTE: Type instances are unique, we can use identity here
            self.type is other.type
            and self.params == other.params
            and self.is_const == other.is_const
        )


class Never:
    """
    Indicator that a FunctionBodyItem never returns.
    Examples for which this is useful: return, continue, break, exit
    """

    ...


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


class WhileLoop(FunctionBodyItem):
    def __init__(
        self,
        condition: FunctionBody,
        body: FunctionBody,
        parsed: parser.WhileLoop,
    ) -> None:
        self.condition = condition
        self.body = body
        super().__init__(parsed.position)


class CallVariable(FunctionBodyItem):
    def __init__(self, name: str, position: Position) -> None:
        self.name = name
        super().__init__(position)


class CallFunction(FunctionBodyItem):
    def __init__(
        self, function: Function, type_params: List[VariableType], position: Position
    ) -> None:
        self.function = function
        self.type_params = type_params
        super().__init__(position)


class CallType(FunctionBodyItem):
    def __init__(self, var_type: VariableType) -> None:
        self.var_type = var_type
        super().__init__(var_type.position)


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


class ForeachLoop(FunctionBodyItem):
    def __init__(self, parsed: parser.ForeachLoop, body: FunctionBody) -> None:
        self.body = body
        super().__init__(parsed.position)


class Variable(FunctionBodyItem):
    def __init__(self, parsed: parser.Identifier, is_func_arg: bool) -> None:
        self.name = parsed.name
        self.is_func_arg = is_func_arg
        super().__init__(parsed.position)


class Assignment(FunctionBodyItem):
    def __init__(
        self, parsed: parser.Assignment, variables: List[Variable], body: FunctionBody
    ) -> None:
        self.variables = variables
        self.body = body
        super().__init__(parsed.position)


class UseBlock(FunctionBodyItem):
    def __init__(
        self, parsed: parser.UseBlock, variables: List[Variable], body: FunctionBody
    ) -> None:
        self.variables = variables
        self.body = body
        super().__init__(parsed.position)


class MatchBlock(FunctionBodyItem):
    def __init__(
        self, position: Position, blocks: List[CaseBlock | DefaultBlock]
    ) -> None:
        self.blocks = blocks
        super().__init__(position)


class CaseBlock(AaaCrossReferenceModel):  # NOTE: This is NOT a FunctionBodyItem
    def __init__(
        self, position: Position, enum_type: Type, variant_name: str, body: FunctionBody
    ) -> None:
        self.enum_type = enum_type
        self.variant_name = variant_name
        self.body = body
        super().__init__(position)


class DefaultBlock(AaaCrossReferenceModel):  # NOTE: This is NOT a FunctionBodyItem
    def __init__(self, position: Position, body: FunctionBody) -> None:
        self.body = body
        super().__init__(position)


class Return(FunctionBodyItem):
    def __init__(self, parsed: parser.Return) -> None:
        super().__init__(parsed.position)


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

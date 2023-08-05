from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from aaa import AaaModel, Position


class AaaParseModel(AaaModel):
    def __init__(self, position: Position) -> None:
        self.position = position


class IntegerLiteral(AaaParseModel):
    def __init__(self, position: Position, value: int) -> None:
        self.value = value
        super().__init__(position)


class StringLiteral(AaaParseModel):
    def __init__(self, position: Position, value: str) -> None:
        self.value = value
        super().__init__(position)


class BooleanLiteral(AaaParseModel):
    def __init__(self, position: Position, value: bool) -> None:
        self.value = value
        super().__init__(position)


class WhileLoop(AaaParseModel):
    def __init__(
        self, position: Position, condition: FunctionBody, body: FunctionBody
    ) -> None:
        self.condition = condition
        self.body = body
        super().__init__(position)


class Identifier(AaaParseModel):
    def __init__(self, position: Position, name: str) -> None:
        self.name = name
        super().__init__(position)


class Branch(AaaParseModel):
    def __init__(
        self,
        position: Position,
        condition: FunctionBody,
        if_body: FunctionBody,
        else_body: Optional[FunctionBody],
    ) -> None:
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body
        super().__init__(position)


class FunctionBody(AaaParseModel):
    def __init__(self, position: Position, items: List[FunctionBodyItem]) -> None:
        self.items = items
        super().__init__(position)


class StructFieldQuery(AaaParseModel):
    def __init__(
        self, position: Position, field_name: StringLiteral, operator_position: Position
    ) -> None:
        self.field_name = field_name
        self.operator_position = operator_position
        super().__init__(position)


class StructFieldUpdate(AaaParseModel):
    def __init__(
        self,
        position: Position,
        field_name: StringLiteral,
        new_value_expr: FunctionBody,
        operator_position: Position,
    ) -> None:
        self.field_name = field_name
        self.new_value_expr = new_value_expr
        self.operator_position = operator_position
        super().__init__(position)


class GetFunctionPointer(AaaParseModel):
    def __init__(self, position: Position, function_name: StringLiteral):
        self.function_name = function_name
        super().__init__(position)


class Return(AaaParseModel):
    ...


class Call(AaaParseModel):
    ...


class Argument(AaaParseModel):
    def __init__(
        self, identifier: Identifier, type: TypeLiteral | FunctionPointerTypeLiteral
    ) -> None:
        self.identifier = identifier
        self.type = type
        super().__init__(identifier.position)


class Function(AaaParseModel):
    def __init__(
        self,
        position: Position,
        struct_name: Optional[Identifier],
        func_name: Identifier,
        type_params: List[TypeLiteral],
        arguments: List[Argument],
        return_types: List[TypeLiteral] | Never,
        body: Optional[FunctionBody],
        end_position: Optional[Position],
    ) -> None:
        self.struct_name = struct_name
        self.func_name = func_name
        self.type_params = type_params
        self.arguments = arguments
        self.return_types = return_types
        self.body = body
        self.end_position = end_position
        super().__init__(position)

    def is_test(self) -> bool:  # pragma: nocover
        return not self.struct_name and self.func_name.name.startswith("test_")


class ImportItem(AaaParseModel):
    def __init__(
        self, position: Position, origninal: Identifier, imported: Identifier
    ) -> None:
        self.original = origninal
        self.imported = imported
        super().__init__(position)


class Import(AaaParseModel):
    def __init__(
        self, position: Position, source: str, imported_items: List[ImportItem]
    ) -> None:
        self.source = source

        source_path = Path(self.source)

        if source_path.is_file() and self.source.endswith(".aaa"):  # pragma: nocover
            self.source_file = source_path
        else:
            self.source_file = position.file.parent / (
                source.replace(".", os.sep) + ".aaa"
            )

        self.imported_items = imported_items
        super().__init__(position)


class Struct(AaaParseModel):
    def __init__(
        self, position: Position, identifier: Identifier, fields: Dict[str, TypeLiteral]
    ) -> None:
        self.identifier = identifier
        self.fields = fields
        super().__init__(position)


class ParsedFile(AaaParseModel):
    def __init__(
        self,
        position: Position,
        functions: List[Function],
        imports: List[Import],
        structs: List[Struct],
        types: List[TypeLiteral],
        enums: List[Enum],
    ) -> None:
        self.functions = functions
        self.imports = imports
        self.structs = structs
        self.types = types
        self.enums = enums
        super().__init__(position)

    def dependencies(self) -> List[Path]:
        return [import_.source_file for import_ in self.imports]


class TypeLiteral(AaaParseModel):
    def __init__(
        self,
        position: Position,
        identifier: Identifier,
        params: List[TypeLiteral],
        const: bool,
    ) -> None:
        self.identifier = identifier
        self.params = params
        self.const = const
        super().__init__(position)


class FunctionPointerTypeLiteral(AaaParseModel):
    def __init__(
        self,
        position: Position,
        argument_types: List[TypeLiteral | FunctionPointerTypeLiteral],
        return_types: List[TypeLiteral | FunctionPointerTypeLiteral],
    ) -> None:
        self.argument_types = argument_types
        self.return_types = return_types
        super().__init__(position)


class FunctionName(AaaParseModel):
    def __init__(
        self,
        position: Position,
        struct_name: Optional[Identifier],
        type_params: List[TypeLiteral],
        func_name: Identifier,
    ) -> None:
        self.struct_name = struct_name
        self.type_params = type_params
        self.func_name = func_name
        super().__init__(position)


class FunctionCall(AaaParseModel):
    def __init__(
        self,
        position: Position,
        struct_name: Optional[Identifier],
        type_params: List[TypeLiteral],
        func_name: Identifier,
    ) -> None:
        self.struct_name = struct_name
        self.type_params = type_params
        self.func_name = func_name
        super().__init__(position)

    def name(self) -> str:
        if self.struct_name:
            return f"{self.struct_name.name}:{self.func_name.name}"
        return self.func_name.name


class CaseLabel(AaaParseModel):
    def __init__(
        self,
        position: Position,
        enum_name: Identifier,
        variant_name: Identifier,
        variables: List[Identifier],
    ) -> None:
        self.enum_name = enum_name
        self.variant_name = variant_name
        self.variables = variables
        super().__init__(position)


class ForeachLoop(AaaParseModel):
    def __init__(self, position: Position, body: FunctionBody) -> None:
        self.body = body
        super().__init__(position)


class UseBlock(AaaParseModel):
    def __init__(
        self, position: Position, variables: List[Identifier], body: FunctionBody
    ) -> None:
        self.variables = variables
        self.body = body
        super().__init__(position)


class Assignment(AaaParseModel):
    def __init__(
        self, position: Position, variables: List[Identifier], body: FunctionBody
    ) -> None:
        self.variables = variables
        self.body = body
        super().__init__(position)


class CaseBlock(AaaParseModel):
    def __init__(
        self, position: Position, label: CaseLabel, body: FunctionBody
    ) -> None:
        self.label = label
        self.body = body
        super().__init__(position)


class DefaultBlock(AaaParseModel):
    def __init__(self, position: Position, body: FunctionBody) -> None:
        self.body = body
        super().__init__(position)


class MatchBlock(AaaParseModel):
    def __init__(
        self, position: Position, blocks: List[CaseBlock | DefaultBlock]
    ) -> None:
        self.blocks = blocks
        super().__init__(position)


class EnumVariant(AaaParseModel):
    def __init__(
        self,
        position: Position,
        name: Identifier,
        associated_data: List[TypeLiteral | FunctionPointerTypeLiteral],
    ) -> None:
        self.name = name
        self.associated_data = associated_data
        super().__init__(position)


class Enum(AaaParseModel):
    def __init__(
        self, position: Position, name: Identifier, variants: List[EnumVariant]
    ) -> None:
        self.identifier = name
        self.variants = variants
        super().__init__(position)


class Never(AaaParseModel):
    ...


FunctionBodyItem = (
    Assignment
    | BooleanLiteral
    | Branch
    | Call
    | CaseBlock
    | CaseLabel
    | DefaultBlock
    | Enum
    | EnumVariant
    | ForeachLoop
    | FunctionCall
    | FunctionName
    | GetFunctionPointer
    | Identifier
    | IntegerLiteral
    | MatchBlock
    | Return
    | StringLiteral
    | StructFieldQuery
    | StructFieldUpdate
    | UseBlock
    | WhileLoop
)


class ParserOutput(AaaModel):
    def __init__(
        self,
        parsed: Dict[Path, ParsedFile],
        entrypoint: Path,
        builtins_path: Path,
    ) -> None:
        self.parsed = parsed
        self.entrypoint = entrypoint
        self.builtins_path = builtins_path

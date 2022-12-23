from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from aaa import AaaModel, Position


class AaaParseModel(AaaModel):
    def __init__(self, position: Position) -> None:
        self.position = position

    def __eq__(self, other: object) -> bool:
        if type(other) != type(self):
            return False

        return vars(self) == vars(other)


class FunctionBodyItem(AaaParseModel):
    ...


class IntegerLiteral(FunctionBodyItem):
    def __init__(self, position: Position, value: int) -> None:
        self.value = value
        super().__init__(position)


class StringLiteral(FunctionBodyItem):
    def __init__(self, position: Position, value: str) -> None:
        self.value = value
        super().__init__(position)


class BooleanLiteral(FunctionBodyItem):
    def __init__(self, position: Position, value: bool) -> None:
        self.value = value
        super().__init__(position)


class Loop(FunctionBodyItem):
    def __init__(
        self, position: Position, condition: FunctionBody, body: FunctionBody
    ) -> None:
        self.condition = condition
        self.body = body
        super().__init__(position)


class Identifier(FunctionBodyItem):
    def __init__(self, position: Position, name: str) -> None:
        self.name = name
        super().__init__(position)


class Branch(FunctionBodyItem):
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


class StructFieldQuery(FunctionBodyItem):
    def __init__(self, position: Position, field_name: StringLiteral) -> None:
        self.field_name = field_name
        super().__init__(position)


class StructFieldUpdate(FunctionBodyItem):
    def __init__(
        self,
        position: Position,
        field_name: StringLiteral,
        new_value_expr: FunctionBody,
    ) -> None:
        self.field_name = field_name
        self.new_value_expr = new_value_expr
        super().__init__(position)


class Argument(AaaParseModel):
    def __init__(
        self, position: Position, identifier: Identifier, type: TypeLiteral
    ) -> None:
        self.identifier = identifier
        self.type = type
        super().__init__(position)


class Function(AaaParseModel):
    def __init__(
        self,
        position: Position,
        struct_name: Optional[Identifier],
        func_name: Identifier,
        type_params: List[TypeLiteral],
        arguments: List[Argument],
        return_types: List[TypeLiteral],
        body: FunctionBody,
    ) -> None:
        self.struct_name = struct_name
        self.func_name = func_name
        self.type_params = type_params
        self.arguments = arguments
        self.return_types = return_types
        self.body = body  # TODO make optional
        super().__init__(position)

    def is_test(self) -> bool:
        return not self.struct_name and self.func_name.name.startswith("test_")


class ImportItem(AaaParseModel):
    def __init__(
        self, position: Position, origninal_name: str, imported_name: str
    ) -> None:
        # TODO inconsisted typing, original_name and imported_name should be an Identifier
        self.original_name = origninal_name
        self.imported_name = imported_name
        super().__init__(position)


class Import(AaaParseModel):
    def __init__(
        self, position: Position, source: str, imported_items: List[ImportItem]
    ) -> None:
        self.source = source

        source_path = Path(self.source)

        if source_path.is_file() and self.source.endswith(".aaa"):
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
    ) -> None:
        self.functions = functions
        self.imports = imports
        self.structs = structs
        self.types = types
        super().__init__(position)

    def dependencies(self) -> List[Path]:
        return [import_.source_file for import_ in self.imports]


class TypeLiteral(AaaParseModel):
    def __init__(
        self, position: Position, identifier: Identifier, params: List[TypeLiteral]
    ) -> None:
        self.identifier = identifier
        self.params = params
        super().__init__(position)


class FunctionName(FunctionBodyItem):
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

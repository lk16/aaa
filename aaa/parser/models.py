from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from aaa import AaaModel


class AaaParseModel(AaaModel):
    def __init__(self, *, file: Path, line: int, column: int) -> None:
        self.file = file
        self.line = line
        self.column = column

    def __eq__(self, other: object) -> bool:
        if type(other) != type(self):
            return False

        return vars(self) == vars(other)


class FunctionBodyItem(AaaParseModel):
    ...


class IntegerLiteral(FunctionBodyItem):
    def __init__(self, *, value: int, file: Path, line: int, column: int) -> None:
        self.value = value
        super().__init__(file=file, line=line, column=column)


class StringLiteral(FunctionBodyItem):
    def __init__(self, *, value: str, file: Path, line: int, column: int) -> None:
        self.value = value
        super().__init__(file=file, line=line, column=column)


class BooleanLiteral(FunctionBodyItem):
    def __init__(self, *, value: bool, file: Path, line: int, column: int) -> None:
        self.value = value
        super().__init__(file=file, line=line, column=column)


class Operator(FunctionBodyItem):
    def __init__(self, *, value: str, file: Path, line: int, column: int) -> None:
        self.value = value
        super().__init__(file=file, line=line, column=column)


class Loop(FunctionBodyItem):
    def __init__(
        self,
        *,
        condition: FunctionBody,
        body: FunctionBody,
        file: Path,
        line: int,
        column: int,
    ) -> None:
        self.condition = condition
        self.body = body
        super().__init__(file=file, line=line, column=column)


class Identifier(FunctionBodyItem):
    def __init__(self, *, name: str, file: Path, line: int, column: int) -> None:
        self.name = name
        super().__init__(file=file, line=line, column=column)


class Branch(FunctionBodyItem):
    def __init__(
        self,
        *,
        condition: FunctionBody,
        if_body: FunctionBody,
        else_body: Optional[FunctionBody],
        file: Path,
        line: int,
        column: int,
    ) -> None:
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body
        super().__init__(file=file, line=line, column=column)


class FunctionBody(
    AaaParseModel
):  # TODO remove this and replace by List[FunctionBodyItem]
    def __init__(
        self, *, items: List[FunctionBodyItem], file: Path, line: int, column: int
    ) -> None:
        self.items = items
        super().__init__(file=file, line=line, column=column)


class StructFieldQuery(FunctionBodyItem):
    def __init__(
        self, *, field_name: StringLiteral, file: Path, line: int, column: int
    ) -> None:
        self.field_name = field_name
        super().__init__(file=file, line=line, column=column)


class StructFieldUpdate(FunctionBodyItem):
    def __init__(
        self,
        *,
        field_name: StringLiteral,
        new_value_expr: FunctionBody,
        file: Path,
        line: int,
        column: int,
    ) -> None:
        self.field_name = field_name
        self.new_value_expr = new_value_expr
        super().__init__(file=file, line=line, column=column)


class Argument(AaaParseModel):
    def __init__(
        self,
        *,
        identifier: Identifier,
        type: TypeLiteral,
        file: Path,
        line: int,
        column: int,
    ) -> None:
        self.identifier = identifier
        self.type = type
        super().__init__(file=file, line=line, column=column)


class Function(AaaParseModel):
    def __init__(
        self,
        *,
        struct_name: Optional[Identifier],
        func_name: Identifier,
        type_params: List[TypeLiteral],
        arguments: List[Argument],
        return_types: List[TypeLiteral],
        body: FunctionBody,
        file: Path,
        line: int,
        column: int,
    ) -> None:
        self.struct_name = struct_name
        self.func_name = func_name
        self.type_params = type_params
        self.arguments = arguments
        self.return_types = return_types
        self.body = body  # TODO make optional
        super().__init__(file=file, line=line, column=column)

    def is_test(self) -> bool:
        return not self.struct_name and self.func_name.name.startswith("test_")


class ImportItem(AaaParseModel):
    def __init__(
        self,
        *,
        origninal_name: str,
        imported_name: str,
        file: Path,
        line: int,
        column: int,
    ) -> None:
        # TODO inconsisted typing, original_name and imported_name should be an Identifier
        self.original_name = origninal_name
        self.imported_name = imported_name
        super().__init__(file=file, line=line, column=column)


class Import(AaaParseModel):
    def __init__(
        self,
        *,
        source: str,
        imported_items: List[ImportItem],
        file: Path,
        line: int,
        column: int,
    ) -> None:
        self.source = source

        source_path = Path(self.source)

        if source_path.is_file() and self.source.endswith(".aaa"):
            self.source_file = source_path
        else:
            self.source_file = file.parent / (source.replace(".", os.sep) + ".aaa")

        self.imported_items = imported_items
        super().__init__(file=file, line=line, column=column)


class Struct(AaaParseModel):
    def __init__(
        self,
        *,
        identifier: Identifier,
        fields: Dict[str, TypeLiteral],
        file: Path,
        line: int,
        column: int,
    ) -> None:
        self.identifier = identifier
        self.fields = fields
        super().__init__(file=file, line=line, column=column)


class ParsedFile(AaaParseModel):
    def __init__(
        self,
        *,
        functions: List[Function],
        imports: List[Import],
        structs: List[Struct],
        types: List[TypeLiteral],
        file: Path,
        line: int,
        column: int,
    ) -> None:
        self.functions = functions
        self.imports = imports
        self.structs = structs
        self.types = types
        super().__init__(file=file, line=line, column=column)


class TypeLiteral(AaaParseModel):
    def __init__(
        self,
        *,
        identifier: Identifier,
        params: List[TypeLiteral],
        file: Path,
        line: int,
        column: int,
    ) -> None:
        self.identifier = identifier
        self.params = params
        super().__init__(file=file, line=line, column=column)


class FunctionName(FunctionBodyItem):
    def __init__(
        self,
        func_name: Identifier,
        type_params: List[TypeLiteral],
        struct_name: Optional[Identifier],
        file: Path,
        line: int,
        column: int,
    ) -> None:
        self.func_name = func_name
        self.type_params = type_params
        self.struct_name = struct_name
        super().__init__(file=file, line=line, column=column)


class ParserOutput(AaaModel):
    def __init__(
        self,
        *,
        parsed: Dict[Path, ParsedFile],
        entrypoint: Path,
        builtins_path: Path,
    ) -> None:
        self.parsed = parsed
        self.entrypoint = entrypoint
        self.builtins_path = builtins_path

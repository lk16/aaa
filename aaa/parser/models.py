from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from lark.lexer import Token

from aaa import AaaModel
from aaa.parser.exceptions import ParserBaseException


class AaaParseModel(AaaModel):
    def __init__(self, *, file: Path, token: Token) -> None:
        self.file = file
        self.token = token


class FunctionBodyItem(AaaParseModel):
    ...


class IntegerLiteral(FunctionBodyItem):
    def __init__(self, *, value: int, file: Path, token: Token) -> None:
        self.value = value
        super().__init__(file=file, token=token)


class StringLiteral(FunctionBodyItem):
    def __init__(self, *, value: str, file: Path, token: Token) -> None:
        self.value = value
        super().__init__(file=file, token=token)


class BooleanLiteral(FunctionBodyItem):
    def __init__(self, *, value: bool, file: Path, token: Token) -> None:
        self.value = value
        super().__init__(file=file, token=token)


class Operator(FunctionBodyItem):
    def __init__(self, *, value: str, file: Path, token: Token) -> None:
        self.value = value
        super().__init__(file=file, token=token)


class Loop(FunctionBodyItem):
    def __init__(
        self, *, condition: FunctionBody, body: FunctionBody, file: Path, token: Token
    ) -> None:
        self.condition = condition
        self.body = body
        super().__init__(file=file, token=token)


class Identifier(FunctionBodyItem):
    def __init__(self, *, name: str, file: Path, token: Token) -> None:
        self.name = name
        super().__init__(file=file, token=token)


class Branch(FunctionBodyItem):
    def __init__(
        self,
        *,
        condition: FunctionBody,
        if_body: FunctionBody,
        else_body: FunctionBody,
        file: Path,
        token: Token,
    ) -> None:
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body
        super().__init__(file=file, token=token)


class FunctionBody(AaaParseModel):
    def __init__(
        self, *, items: List[FunctionBodyItem], file: Path, token: Token
    ) -> None:
        self.items = items
        super().__init__(file=file, token=token)


class StructFieldQuery(FunctionBodyItem):
    def __init__(self, *, field_name: StringLiteral, file: Path, token: Token) -> None:
        self.field_name = field_name
        super().__init__(file=file, token=token)


class StructFieldUpdate(FunctionBodyItem):
    def __init__(
        self,
        *,
        field_name: StringLiteral,
        new_value_expr: FunctionBody,
        file: Path,
        token: Token,
    ) -> None:
        self.field_name = field_name
        self.new_value_expr = new_value_expr
        super().__init__(file=file, token=token)


class Argument(AaaParseModel):
    def __init__(
        self, *, identifier: Identifier, type: TypeLiteral, file: Path, token: Token
    ) -> None:
        self.identifier = identifier
        self.type = type
        super().__init__(file=file, token=token)


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
        token: Token,
    ) -> None:
        self.struct_name = struct_name
        self.func_name = func_name
        self.type_params = type_params
        self.arguments = arguments
        self.return_types = return_types
        self.body = body
        super().__init__(file=file, token=token)


class ImportItem(AaaParseModel):
    def __init__(
        self, *, origninal_name: str, imported_name: str, file: Path, token: Token
    ) -> None:
        self.original_name = origninal_name
        self.imported_name = imported_name
        super().__init__(file=file, token=token)


class Import(AaaParseModel):
    def __init__(
        self, *, source: str, imported_items: List[ImportItem], file: Path, token: Token
    ) -> None:
        self.source = source
        self.imported_items = imported_items
        super().__init__(file=file, token=token)


class Struct(AaaParseModel):
    def __init__(
        self,
        *,
        identifier: Identifier,
        fields: Dict[str, TypeLiteral],
        file: Path,
        token: Token,
    ) -> None:
        self.identifier = identifier
        self.fields = fields
        super().__init__(file=file, token=token)


class ParsedFile(AaaParseModel):
    def __init__(
        self,
        *,
        functions: List[Function],
        imports: List[Import],
        structs: List[Struct],
        types: List[TypeLiteral],
        file: Path,
        token: Token,
    ) -> None:
        self.functions = functions
        self.imports = imports
        self.structs = structs
        self.types = types
        super().__init__(file=file, token=token)


class TypeLiteral(AaaParseModel):
    def __init__(
        self,
        *,
        identifier: Identifier,
        params: List[TypeLiteral],
        file: Path,
        token: Token,
    ) -> None:
        self.identifier = identifier
        self.params = params
        super().__init__(file=file, token=token)


class FunctionName(AaaParseModel):
    def __init__(
        self,
        func_name: Identifier,
        type_params: List[TypeLiteral],
        struct_name: Optional[Identifier],
        file: Path,
        token: Token,
    ) -> None:
        self.func_name = func_name
        self.type_params = type_params
        self.struct_name = struct_name
        super().__init__(file=file, token=token)


class ParserOutput(AaaModel):
    def __init__(
        self,
        *,
        parsed: Dict[Path, ParsedFile],
        entrypoint: Path,
        builtins_path: Path,
        exceptions: List[ParserBaseException],
    ) -> None:
        self.parsed = parsed
        self.entrypoint = entrypoint
        self.builtins_path = builtins_path
        self.exceptions = exceptions

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from lark.lexer import Token

from aaa import AaaModel
from aaa.parser.exceptions import ParserBaseException


class AaaParseModel(AaaModel):
    def __init__(self, *, token: Token) -> None:
        self.token = token


class FunctionBodyItem(AaaParseModel):
    ...


class IntegerLiteral(FunctionBodyItem):
    def __init__(self, *, value: int, token: Token) -> None:
        self.value = value
        super().__init__(token=token)


class StringLiteral(FunctionBodyItem):
    def __init__(self, *, value: str, token: Token) -> None:
        self.value = value
        super().__init__(token=token)


class BooleanLiteral(FunctionBodyItem):
    def __init__(self, *, value: bool, token: Token) -> None:
        self.value = value
        super().__init__(token=token)


class Operator(FunctionBodyItem):
    def __init__(self, *, value: str, token: Token) -> None:
        self.value = value
        super().__init__(token=token)


class Loop(FunctionBodyItem):
    def __init__(
        self, *, condition: FunctionBody, body: FunctionBody, token: Token
    ) -> None:
        self.condition = condition
        self.body = body
        super().__init__(token=token)


class LoopCondition(AaaParseModel):
    def __init__(self, *, value: FunctionBody, token: Token) -> None:
        self.value = value
        super().__init__(token=token)


class LoopBody(AaaParseModel):
    def __init__(self, *, value: FunctionBody, token: Token) -> None:
        self.value = value
        super().__init__(token=token)


class Identifier(FunctionBodyItem):
    def __init__(self, *, name: str, token: Token) -> None:
        self.name = name
        super().__init__(token=token)


class Branch(FunctionBodyItem):
    def __init__(
        self,
        *,
        condition: FunctionBody,
        if_body: FunctionBody,
        else_body: FunctionBody,
        token: Token,
    ) -> None:
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body
        super().__init__(token=token)


class FunctionBody(AaaParseModel):
    def __init__(self, *, items: Sequence[FunctionBodyItem], token: Token) -> None:
        self.items = items
        super().__init__(token=token)


class BranchCondition(FunctionBody):
    ...


class BranchIfBody(FunctionBody):
    ...


class BranchElseBody(FunctionBody):
    ...


class MemberFunctionLiteral(FunctionBodyItem):
    def __init__(
        self, *, struct_name: TypeLiteral, func_name: Identifier, token: Token
    ) -> None:
        self.struct_name = struct_name
        self.func_name = func_name
        super().__init__(token=token)


class StructFieldQuery(FunctionBodyItem):
    def __init__(self, *, field_name: StringLiteral, token: Token) -> None:
        self.field_name = field_name
        super().__init__(token=token)


class StructFieldUpdate(FunctionBodyItem):
    def __init__(
        self, *, field_name: StringLiteral, new_value_expr: FunctionBody, token: Token
    ) -> None:
        self.field_name = field_name
        self.new_value_expr = new_value_expr
        super().__init__(token=token)


class Argument(AaaParseModel):
    def __init__(
        self, *, identifier: Identifier, type: TypeLiteral, token: Token
    ) -> None:
        self.identifier = identifier
        self.type = type
        super().__init__(token=token)


class Function(AaaParseModel):
    def __init__(
        self,
        *,
        name: MemberFunctionLiteral | Identifier,
        type_params: List[TypeLiteral],
        arguments: Dict[str, Argument],
        return_types: List[TypeLiteral],
        body: FunctionBody,
        token: Token,
    ) -> None:
        self.name = name
        self.type_params = type_params
        self.arguments = arguments
        self.return_types = return_types
        self.body = body
        super().__init__(token=token)

    def get_names(self) -> Tuple[str, str]:
        if isinstance(self.name, Identifier):
            struct_name = ""
            func_name = self.name.name
        elif isinstance(self.name, MemberFunctionLiteral):
            struct_name = self.name.struct_name.identifier.name
            func_name = self.name.func_name.name
        else:  # pragma: nocover
            assert False

        return struct_name, func_name

    def get_type_param(self, name: str) -> Optional[TypeLiteral]:
        for type_param in self.type_params:
            if type_param.identifier.name == name:
                return type_param
        return None


class ImportItem(AaaParseModel):
    def __init__(
        self, *, origninal_name: str, imported_name: str, token: Token
    ) -> None:
        self.original_name = origninal_name
        self.imported_name = imported_name
        super().__init__(token=token)


class Import(AaaParseModel):
    def __init__(
        self, *, source: str, imported_items: List[ImportItem], token: Token
    ) -> None:
        self.source = source
        self.imported_items = imported_items
        super().__init__(token=token)


class Struct(AaaParseModel):
    def __init__(
        self, *, identifier: Identifier, fields: Dict[str, TypeLiteral], token: Token
    ) -> None:
        self.identifier = identifier
        self.fields = fields


class ParsedFile(AaaParseModel):
    def __init__(
        self,
        *,
        functions: List[Function],
        imports: List[Import],
        structs: List[Struct],
        types: List[TypeLiteral],
        token: Token,
    ) -> None:
        self.functions = functions
        self.imports = imports
        self.structs = structs
        self.types = types
        super().__init__(token=token)


class TypeLiteral(AaaParseModel):
    def __init__(
        self, *, identifier: Identifier, params: TypeParameters, token: Token
    ) -> None:
        self.identifier = identifier
        self.params = params
        super().__init__(token=token)


class TypeParameters(AaaParseModel):
    def __init__(self, *, value: List[TypeLiteral], token: Token) -> None:
        self.value = value


class ParserOutput(AaaModel):
    def __init__(
        self,
        *,
        parsed: Dict[Path, ParsedFile],
        builtins_path: Path,
        exceptions: List[ParserBaseException],
    ) -> None:
        self.parsed = parsed
        self.builtins_path = builtins_path
        self.exceptions = exceptions

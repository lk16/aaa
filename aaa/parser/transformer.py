from pathlib import Path
from typing import Any, List, Optional, Union

from lark.lexer import Token
from lark.visitors import Transformer, v_args

from aaa.parser.models import (
    Argument,
    BooleanLiteral,
    Branch,
    Function,
    FunctionBody,
    FunctionBodyItem,
    FunctionName,
    Identifier,
    Import,
    ImportItem,
    IntegerLiteral,
    Loop,
    LoopBody,
    LoopCondition,
    Operator,
    ParsedFile,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    TypeLiteral,
)

DUMMY_TOKEN = Token(type_="", value="")  # type: ignore


@v_args(inline=True)
class AaaTransformer(Transformer[Any, ParsedFile]):
    def __init__(self, file: Path) -> None:
        self.file = file
        super().__init__()

    def arguments(self, *arguments: Argument) -> List[Argument]:
        return list(arguments)

    def argument(self, identifier: Identifier, type: TypeLiteral) -> Argument:
        return Argument(
            token=identifier.token, identifier=identifier, type=type, file=self.file
        )

    def boolean(self, token: Token) -> BooleanLiteral:
        assert token.value in ["true", "false"]
        value = token.value == "true"
        return BooleanLiteral(token=token, value=value, file=self.file)

    def branch(
        self,
        if_token: Token,
        condition: FunctionBody,
        if_body_begin_token: Token,
        if_body: FunctionBody,
        else_token: Optional[Token],
        else_body_begin_token: Optional[Token],
        else_body: Optional[FunctionBody],
    ) -> Branch:
        else_body = else_body or FunctionBody(
            token=DUMMY_TOKEN, items=[], file=self.file
        )

        return Branch(
            token=if_token,
            condition=condition,
            if_body=if_body,
            else_body=else_body,
            file=self.file,
        )

    def builtin_function_declaration(
        self,
        token: Token,
        builtin_function_name: FunctionName,
        arguments: Optional[List[Argument]],
        return_types: Optional[List[TypeLiteral]],
    ) -> Function:
        arguments = arguments or []
        return_types = return_types or []
        empty_body = FunctionBody(items=[], file=self.file, token=DUMMY_TOKEN)

        return Function(
            struct_name=builtin_function_name.struct_name,
            func_name=builtin_function_name.func_name,
            type_params=builtin_function_name.type_params,
            arguments=arguments,
            return_types=return_types,
            body=empty_body,
            file=self.file,
            token=token,
        )

    def builtin_type_declaration(
        self,
        token: Token,
        type_literal: TypeLiteral,
    ) -> TypeLiteral:
        return type_literal

    def builtins_file_root(self, *args: Function | TypeLiteral) -> ParsedFile:
        functions: List[Function] = []
        types: List[TypeLiteral] = []

        for arg in args:
            if isinstance(arg, Function):
                functions.append(arg)
            elif isinstance(arg, TypeLiteral):
                types.append(arg)
            else:  # pragma: nocover
                assert False

        return ParsedFile(
            token=args[0].token,
            functions=functions,
            imports=[],
            structs=[],
            types=types,
            file=self.file,
        )

    def function_body_item(
        self, function_body_item: FunctionBodyItem
    ) -> FunctionBodyItem:
        return function_body_item

    def function_body(self, *function_body_items: FunctionBodyItem) -> FunctionBody:
        token = function_body_items[0].token
        return FunctionBody(
            token=token, items=list(function_body_items), file=self.file
        )

    def function_name(
        self,
        type_literal: TypeLiteral,
        identifier: Optional[Identifier],
    ) -> FunctionName:
        if identifier:
            return FunctionName(
                struct_name=type_literal.identifier,
                type_params=type_literal.params,
                func_name=identifier,
                file=self.file,
                token=type_literal.token,
            )

        return FunctionName(
            struct_name=None,
            type_params=type_literal.params,
            func_name=type_literal.identifier,
            file=self.file,
            token=type_literal.token,
        )

    def function_definition(
        self,
        token: Token,
        name: FunctionName,
        arguments: Optional[List[Argument]],
        return_types: Optional[List[TypeLiteral]],
        body_begin_token: Token,
        body: FunctionBody,
    ) -> Function:
        arguments = arguments or []
        return_types = return_types or []

        return Function(
            token=token,
            struct_name=name.struct_name,
            func_name=name.func_name,
            type_params=name.type_params,
            arguments=arguments,
            return_types=return_types,
            body=body,
            file=self.file,
        )

    def identifier(self, token: Token) -> Identifier:
        return Identifier(name=token.value, token=token, file=self.file)

    def type_literal(
        self,
        identifier: Identifier,
        params: Optional[List[TypeLiteral]],
    ) -> TypeLiteral:
        params = params or []

        return TypeLiteral(
            identifier=identifier, params=params, file=self.file, token=identifier.token
        )

    def import_item(
        self, original_name: Identifier, imported_name: Optional[Identifier] = None
    ) -> ImportItem:
        if imported_name is None:
            imported_name = original_name

        return ImportItem(
            origninal_name=original_name.name,
            imported_name=imported_name.name,
            token=original_name.token,
            file=self.file,
        )

    def import_items(self, *import_items: ImportItem) -> List[ImportItem]:
        return list(import_items)

    def import_statement(
        self, token: Token, source: StringLiteral, imported_items: List[ImportItem]
    ) -> Import:
        return Import(
            source=source.value,
            imported_items=imported_items,
            token=token,
            file=self.file,
        )

    def integer(self, token: Token) -> IntegerLiteral:
        return IntegerLiteral(token=token, value=int(token.value), file=self.file)

    def literal(
        self, literal: Union[IntegerLiteral, BooleanLiteral, StringLiteral]
    ) -> Union[IntegerLiteral, BooleanLiteral, StringLiteral]:
        return literal

    def loop(
        self, condition: LoopCondition, begin_token: Token, body: LoopBody
    ) -> Loop:
        return Loop(
            token=condition.token,
            condition=condition.value,
            body=body.value,
            file=self.file,
        )

    def loop_condition(
        self, token: Token, function_body: FunctionBody
    ) -> LoopCondition:
        return LoopCondition(token=token, value=function_body, file=self.file)

    def loop_body(self, function_body: FunctionBody) -> LoopBody:
        return LoopBody(token=function_body.token, value=function_body, file=self.file)

    def member_function_name(self, token: Token) -> Identifier:
        return Identifier(name=token.value, token=token, file=self.file)

    def operator(self, token: Token) -> Operator:
        return Operator(value=token.value, token=token, file=self.file)

    def regular_file_root(self, *args: Function | Struct | Import) -> ParsedFile:
        functions: List[Function] = []
        imports: List[Import] = []
        structs: List[Struct] = []

        for arg in args:
            if isinstance(arg, Function):
                functions.append(arg)
            elif isinstance(arg, Struct):
                structs.append(arg)
            elif isinstance(arg, Import):
                imports.append(arg)
            else:  # pragma: nocover
                assert False

        return ParsedFile(
            token=args[0].token,
            functions=functions,
            imports=imports,
            structs=structs,
            types=[],
            file=self.file,
        )

    def return_types(self, *types: TypeLiteral) -> List[TypeLiteral]:
        return list(types)

    def string(self, token: Token) -> StringLiteral:
        assert len(token.value) >= 2

        value = token.value[1:-1]
        value = value.replace("\\\\", "\\")
        value = value.replace("\\n", "\n")
        value = value.replace('\\"', '"')

        return StringLiteral(token=token, value=value, file=self.file)

    def struct_definition(
        self,
        struct_token: Token,
        identifier: Identifier,
        begin_token: Token,
        fields: List[Argument],
    ) -> Struct:
        return Struct(
            token=struct_token,
            identifier=identifier,
            fields={field.identifier.name: field.type for field in fields},
            file=self.file,
        )

    def struct_field_query_operator(self, token: Token) -> Token:
        return token

    def struct_field_query(
        self, field_name: StringLiteral, token: Token
    ) -> StructFieldQuery:
        return StructFieldQuery(field_name=field_name, token=token, file=self.file)

    def struct_field_update_operator(self, token: Token) -> Token:
        return token

    def struct_field_update(
        self,
        field_name: StringLiteral,
        new_value_expr_token: Token,
        new_value_expr: FunctionBody,
        update_operator_token: Token,
    ) -> StructFieldUpdate:
        return StructFieldUpdate(
            field_name=field_name,
            new_value_expr=new_value_expr,
            token=update_operator_token,
            file=self.file,
        )

    def type_params(self, *params: TypeLiteral) -> List[TypeLiteral]:
        return list(params)

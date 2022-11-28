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
    Operator,
    ParsedFile,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    TypeLiteral,
)


@v_args(inline=True)
class AaaTransformer(Transformer[Any, ParsedFile]):
    def __init__(self, file: Path) -> None:
        self.file = file
        super().__init__()

    def arguments(self, *arguments: Argument) -> List[Argument]:
        return list(arguments)

    def argument(self, identifier: Identifier, type: TypeLiteral) -> Argument:
        return Argument(
            line=identifier.line,
            column=identifier.column,
            identifier=identifier,
            type=type,
            file=self.file,
        )

    def boolean(self, token: Token) -> BooleanLiteral:
        assert token.value in ["true", "false"]
        assert token.line is not None
        assert token.column is not None
        value = token.value == "true"
        return BooleanLiteral(
            line=token.line, column=token.column, value=value, file=self.file
        )

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
            line=-1, column=-1, items=[], file=self.file
        )

        assert if_token.line is not None
        assert if_token.column is not None

        return Branch(
            line=if_token.line,
            column=if_token.column,
            condition=condition,
            if_body=if_body,
            else_body=else_body,
            file=self.file,
        )

    def function_declaration(
        self,
        token: Token,
        function_name: FunctionName,
        arguments: Optional[List[Argument]],
        return_types: Optional[List[TypeLiteral]],
    ) -> Function:
        arguments = arguments or []
        return_types = return_types or []
        empty_body = FunctionBody(items=[], file=self.file, line=-1, column=-1)

        assert token.line is not None
        assert token.column is not None

        return Function(
            struct_name=function_name.struct_name,
            func_name=function_name.func_name,
            type_params=function_name.type_params,
            arguments=arguments,
            return_types=return_types,
            body=empty_body,
            file=self.file,
            line=token.line,
            column=token.column,
        )

    def type_declaration(
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
            line=args[0].line,
            column=args[0].column,
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
        return FunctionBody(
            line=function_body_items[0].line,
            column=function_body_items[0].column,
            items=list(function_body_items),
            file=self.file,
        )

    def function_name(
        self,
        type_literal: TypeLiteral,
        identifier: Optional[Identifier],
    ) -> FunctionName:

        assert type_literal.line is not None
        assert type_literal.column is not None

        if identifier:
            return FunctionName(
                struct_name=type_literal.identifier,
                type_params=type_literal.params,
                func_name=identifier,
                file=self.file,
                line=type_literal.line,
                column=type_literal.column,
            )

        return FunctionName(
            struct_name=None,
            type_params=type_literal.params,
            func_name=type_literal.identifier,
            file=self.file,
            line=type_literal.line,
            column=type_literal.column,
        )

    def function_definition(
        self,
        function_declaration: Function,
        body_begin_token: Token,
        body: FunctionBody,
    ) -> Function:
        function_declaration.body = body
        return function_declaration

    def identifier(self, token: Token) -> Identifier:
        assert token.line is not None
        assert token.column is not None

        return Identifier(
            name=token.value, line=token.line, column=token.column, file=self.file
        )

    def type_literal(
        self,
        identifier: Identifier,
        params: Optional[List[TypeLiteral]],
    ) -> TypeLiteral:
        params = params or []

        return TypeLiteral(
            identifier=identifier,
            params=params,
            file=self.file,
            line=identifier.line,
            column=identifier.column,
        )

    def import_item(
        self, original_name: Identifier, imported_name: Optional[Identifier] = None
    ) -> ImportItem:
        if imported_name is None:
            imported_name = original_name

        return ImportItem(
            origninal_name=original_name.name,
            imported_name=imported_name.name,
            line=original_name.line,
            column=original_name.column,
            file=self.file,
        )

    def import_items(self, *import_items: ImportItem) -> List[ImportItem]:
        return list(import_items)

    def import_statement(
        self, token: Token, source: StringLiteral, imported_items: List[ImportItem]
    ) -> Import:
        assert token.line is not None
        assert token.column is not None

        return Import(
            source=source.value,
            imported_items=imported_items,
            line=token.line,
            column=token.column,
            file=self.file,
        )

    def integer(self, token: Token) -> IntegerLiteral:
        assert token.line is not None
        assert token.column is not None

        return IntegerLiteral(
            line=token.line, column=token.column, value=int(token.value), file=self.file
        )

    def literal(
        self, literal: Union[IntegerLiteral, BooleanLiteral, StringLiteral]
    ) -> Union[IntegerLiteral, BooleanLiteral, StringLiteral]:
        return literal

    def loop(
        self,
        while_token: Token,
        condition: FunctionBody,
        begin_token: Token,
        body: FunctionBody,
    ) -> Loop:
        assert while_token.line is not None
        assert while_token.column is not None

        return Loop(
            line=while_token.line,
            column=while_token.column,
            condition=condition,
            body=body,
            file=self.file,
        )

    def member_function_name(self, token: Token) -> Identifier:
        assert token.line is not None
        assert token.column is not None

        return Identifier(
            name=token.value, line=token.line, column=token.column, file=self.file
        )

    def operator(self, token: Token) -> Operator:
        assert token.line is not None
        assert token.column is not None

        return Operator(
            value=token.value, line=token.line, column=token.column, file=self.file
        )

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
            line=args[0].line,
            column=args[0].column,
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
        # TODO add more escape sequences and tests
        value = value.replace("\\\\", "\\")
        value = value.replace("\\n", "\n")
        value = value.replace("\\r", "\r")
        value = value.replace('\\"', '"')

        assert token.line is not None
        assert token.column is not None

        return StringLiteral(
            line=token.line, column=token.column, value=value, file=self.file
        )

    def struct_definition(
        self,
        struct_token: Token,
        identifier: Identifier,
        begin_token: Token,
        fields: List[Argument],
    ) -> Struct:
        assert struct_token.line is not None
        assert struct_token.column is not None

        return Struct(
            line=struct_token.line,
            column=struct_token.column,
            identifier=identifier,
            fields={field.identifier.name: field.type for field in fields},
            file=self.file,
        )

    def struct_field_query_operator(self, token: Token) -> Token:
        return token

    def struct_field_query(
        self, field_name: StringLiteral, token: Token
    ) -> StructFieldQuery:
        assert token.line is not None
        assert token.column is not None

        return StructFieldQuery(
            field_name=field_name, line=token.line, column=token.column, file=self.file
        )

    def struct_field_update_operator(self, token: Token) -> Token:
        return token

    def struct_field_update(
        self,
        field_name: StringLiteral,
        new_value_expr_token: Token,
        new_value_expr: FunctionBody,
        update_operator_token: Token,
    ) -> StructFieldUpdate:
        assert update_operator_token.line is not None
        assert update_operator_token.column is not None

        return StructFieldUpdate(
            field_name=field_name,
            new_value_expr=new_value_expr,
            line=update_operator_token.line,
            column=update_operator_token.column,
            file=self.file,
        )

    def type_params(self, *params: TypeLiteral) -> List[TypeLiteral]:
        return list(params)

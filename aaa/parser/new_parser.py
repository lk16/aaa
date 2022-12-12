from pathlib import Path
from typing import List, Optional, Tuple

from aaa.parser.exceptions import (
    EndOfFileException,
    NewParserUnhandledTopLevelToken,
    ParserBaseException,
    ParserException,
)
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
    ParsedFile,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    TypeLiteral,
)
from aaa.tokenizer.models import Token, TokenType


class SingleFileParser:
    def __init__(self, file: Path, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.file = file

    def parse_builtins_file(self) -> ParsedFile:
        parsed_file, offset = self._parse_builtins_file_root(0)

        if offset != len(self.tokens):
            token = self.tokens[offset]

            raise NewParserUnhandledTopLevelToken(
                file=self.file,
                line=token.line,
                column=token.column,
                token_type=token.type,
            )

        return parsed_file

    def parse_regular_file(self) -> ParsedFile:
        parsed_file, offset = self._parse_regular_file_root(0)

        if offset != len(self.tokens):
            token = self.tokens[offset]

            raise NewParserUnhandledTopLevelToken(
                file=self.file,
                line=token.line,
                column=token.column,
                token_type=token.type,
            )

        return parsed_file

    def _peek_token(self, offset: int) -> Optional[Token]:
        try:
            return self.tokens[offset]
        except IndexError:
            return None

    def _token(self, offset: int, expected: List[TokenType]) -> Tuple[Token, int]:
        token = self._peek_token(offset)

        if not token:
            raise EndOfFileException(file=self.file)

        if token.type not in expected:
            raise ParserException(
                file=token.file,
                line=token.line,
                column=token.column,
                expected_token_types=expected,
                found_token_type=token.type,
            )

        return token, offset + 1

    def _parse_identifier(self, offset: int) -> Tuple[Identifier, int]:
        token, offset = self._token(offset, [TokenType.IDENTIFIER])

        identifier = Identifier(
            name=token.value, file=token.file, line=token.line, column=token.column
        )

        return identifier, offset

    def _parse_flat_type_params(self, offset: int) -> Tuple[List[TypeLiteral], int]:
        _, offset = self._token(offset, [TokenType.TYPE_PARAM_BEGIN])

        identifiers: List[Identifier] = []
        token: Optional[Token]

        while True:
            identifier, offset = self._parse_identifier(offset)
            identifiers.append(identifier)

            token, offset = self._token(
                offset, [TokenType.TYPE_PARAM_END, TokenType.COMMA]
            )

            if token.type == TokenType.TYPE_PARAM_END:
                break

            # Handle comma at the end, for example `[A,]` or `[A,B,]`
            token = self._peek_token(offset)
            if token and token.type == TokenType.TYPE_PARAM_END:
                _, offset = self._token(offset, [TokenType.TYPE_PARAM_END])
                break

        type_params = [
            TypeLiteral(
                identifier=identifier,
                params=[],
                file=identifier.file,
                line=identifier.line,
                column=identifier.column,
            )
            for identifier in identifiers
        ]

        return type_params, offset

    def _parse_flat_type_literal(self, offset: int) -> Tuple[TypeLiteral, int]:
        identifier, offset = self._parse_identifier(offset)

        type_params: List[TypeLiteral] = []

        try:
            type_params, offset = self._parse_flat_type_params(offset)
        except ParserBaseException:
            pass

        type_literal = TypeLiteral(
            identifier=identifier,
            params=type_params,
            file=identifier.file,
            line=identifier.line,
            column=identifier.column,
        )

        return type_literal, offset

    def _parse_type_declaration(self, offset: int) -> Tuple[TypeLiteral, int]:
        _, offset = self._token(offset, [TokenType.TYPE])
        type_literal, offset = self._parse_flat_type_literal(offset)
        return type_literal, offset

    def _parse_function_name(self, offset: int) -> Tuple[FunctionName, int]:
        type_literal, offset = self._parse_flat_type_literal(offset)
        identifier: Optional[Identifier] = None

        token = self._peek_token(offset)

        if token and token.type == TokenType.COLON:
            _, offset = self._token(offset, [TokenType.COLON])
            identifier, offset = self._parse_identifier(offset)

        struct_name: Optional[Identifier] = None

        if identifier:
            # member function name as in a declaration, such as `vec[T]:clear`
            struct_name = type_literal.identifier
            func_name = identifier

        else:
            # function name as in declaration, such as `dup[A]`
            func_name = type_literal.identifier

        function_name = FunctionName(
            struct_name=struct_name,
            type_params=type_literal.params,
            func_name=func_name,
            file=self.file,
            line=type_literal.line,
            column=type_literal.column,
        )

        return function_name, offset

    def _parse_type_params(self, offset: int) -> Tuple[List[TypeLiteral], int]:
        _, offset = self._token(offset, [TokenType.TYPE_PARAM_BEGIN])

        type_params: List[TypeLiteral] = []
        token: Optional[Token]

        while True:
            type_param, offset = self._parse_type_literal(offset)
            type_params.append(type_param)

            token, offset = self._token(
                offset, [TokenType.TYPE_PARAM_END, TokenType.COMMA]
            )

            if token.type == TokenType.TYPE_PARAM_END:
                break

            # Handle comma at the end, for example `[A,]` or `[A,B[C,],]`
            token = self._peek_token(offset)
            if token and token.type == TokenType.TYPE_PARAM_END:
                _, offset = self._token(offset, [TokenType.TYPE_PARAM_END])
                break

        return type_params, offset

    def _parse_type_literal(self, offset: int) -> Tuple[TypeLiteral, int]:
        identifier, offset = self._parse_identifier(offset)

        type_params: List[TypeLiteral] = []

        try:
            type_params, offset = self._parse_type_params(offset)
        except ParserBaseException:
            pass

        type_literal = TypeLiteral(
            identifier=identifier,
            params=type_params,
            file=identifier.file,
            line=identifier.line,
            column=identifier.column,
        )

        return type_literal, offset

    def _parse_argument(self, offset: int) -> Tuple[Argument, int]:
        identifier, offset = self._parse_identifier(offset)
        _, offset = self._token(offset, [TokenType.AS])
        type, offset = self._parse_type_literal(offset)

        argument = Argument(
            identifier=identifier,
            type=type,
            file=identifier.file,
            line=identifier.line,
            column=identifier.column,
        )

        return argument, offset

    def _parse_arguments(self, offset: int) -> Tuple[List[Argument], int]:
        arguments: List[Argument] = []

        argument, offset = self._parse_argument(offset)
        arguments.append(argument)

        while True:
            try:
                _, offset = self._token(offset, [TokenType.COMMA])
            except ParserBaseException:
                break

            try:
                argument, offset = self._parse_argument(offset)
            except ParserBaseException:
                break
            else:
                arguments.append(argument)

        return arguments, offset

    def _parse_return_types(self, offset: int) -> Tuple[List[TypeLiteral], int]:
        return_types: List[TypeLiteral] = []

        return_type, offset = self._parse_type_literal(offset)
        return_types.append(return_type)

        while True:
            try:
                _, offset = self._token(offset, [TokenType.COMMA])
            except ParserBaseException:
                break

            try:
                return_type, offset = self._parse_type_literal(offset)
            except ParserBaseException:
                break
            else:
                return_types.append(return_type)

        return return_types, offset

    def _parse_function_declaration(self, offset: int) -> Tuple[Function, int]:
        fn_token, offset = self._token(offset, [TokenType.FUNCTION])
        function_name, offset = self._parse_function_name(offset)
        arguments: List[Argument] = []
        return_types: List[TypeLiteral] = []

        token = self._peek_token(offset)
        if token and token.type == TokenType.ARGS:
            _, offset = self._token(offset, [TokenType.ARGS])
            arguments, offset = self._parse_arguments(offset)

        token = self._peek_token(offset)
        if token and token.type == TokenType.RETURN:
            _, offset = self._token(offset, [TokenType.RETURN])
            return_types, offset = self._parse_return_types(offset)

        empty_body = FunctionBody(items=[], file=self.file, line=-1, column=-1)

        function = Function(
            struct_name=function_name.struct_name,
            func_name=function_name.func_name,
            type_params=function_name.type_params,
            arguments=arguments,
            return_types=return_types,
            body=empty_body,
            file=self.file,
            line=fn_token.line,
            column=fn_token.column,
        )

        return function, offset

    def _parse_builtins_file_root(self, offset: int) -> Tuple[ParsedFile, int]:

        first_token = self._peek_token(offset)

        if first_token:
            first_line = first_token.line
            first_column = first_token.column
        else:
            first_line = 1
            first_column = 1

        functions: List[Function] = []
        types: List[TypeLiteral] = []

        while True:
            try:
                function, offset = self._parse_function_declaration(offset)
            except ParserBaseException:
                pass
            else:
                functions.append(function)
                continue

            try:
                type, offset = self._parse_type_declaration(offset)
            except ParserBaseException:
                pass
            else:
                types.append(type)
                continue

            break

        parsed_file = ParsedFile(
            line=first_line,
            column=first_column,
            functions=functions,
            imports=[],
            structs=[],
            types=types,
            file=self.file,
        )

        return parsed_file, offset

    def _parse_struct_definition(self, offset: int) -> Tuple[Struct, int]:
        struct_token, offset = self._token(offset, [TokenType.STRUCT])
        identifier, offset = self._parse_identifier(offset)
        _, offset = self._token(offset, [TokenType.BEGIN])
        fields, offset = self._parse_arguments(offset)
        _, offset = self._token(offset, [TokenType.END])

        struct = Struct(
            line=struct_token.line,
            column=struct_token.column,
            identifier=identifier,
            fields={field.identifier.name: field.type for field in fields},
            file=self.file,
        )

        return struct, offset

    def _parse_string(self, offset: int) -> Tuple[StringLiteral, int]:
        token, offset = self._token(offset, [TokenType.STRING])

        value = token.value[1:-1]
        value = value.replace("\\\\", "\\")
        value = value.replace("\\n", "\n")
        value = value.replace("\\r", "\r")
        value = value.replace('\\"', '"')

        string = StringLiteral(
            value=value, file=token.file, line=token.line, column=token.column
        )

        return string, offset

    def _parse_import_item(self, offset: int) -> Tuple[ImportItem, int]:
        original_name, offset = self._parse_identifier(offset)

        token = self._peek_token(offset)
        if token and token.type == TokenType.AS:
            _, offset = self._token(offset, [TokenType.AS])
            imported_name, offset = self._parse_identifier(offset)
        else:
            imported_name = original_name

        import_item = ImportItem(
            origninal_name=original_name.name,
            imported_name=imported_name.name,
            file=original_name.file,
            line=original_name.line,
            column=original_name.column,
        )

        return import_item, offset

    def _parse_import_items(self, offset: int) -> Tuple[List[ImportItem], int]:
        import_items: List[ImportItem] = []

        import_item, offset = self._parse_import_item(offset)
        import_items.append(import_item)

        while True:
            try:
                _, offset = self._token(offset, [TokenType.COMMA])
            except ParserBaseException:
                break

            try:
                import_item, offset = self._parse_import_item(offset)
            except ParserBaseException:
                break
            else:
                import_items.append(import_item)

        return import_items, offset

    def _parse_import_statement(self, offset: int) -> Tuple[Import, int]:
        from_token, offset = self._token(offset, [TokenType.FROM])
        source, offset = self._parse_string(offset)
        _, offset = self._token(offset, [TokenType.IMPORT])
        import_items, offset = self._parse_import_items(offset)

        import_ = Import(
            source=source.value,
            imported_items=import_items,
            file=from_token.file,
            line=from_token.line,
            column=from_token.column,
        )

        return import_, offset

    def _parse_boolean(self, offset: int) -> Tuple[BooleanLiteral, int]:
        token, offset = self._token(offset, [TokenType.TRUE, TokenType.FALSE])

        boolean = BooleanLiteral(
            value=token.value == "true",
            file=token.file,
            line=token.line,
            column=token.column,
        )

        return boolean, offset

    def _parse_integer(self, offset: int) -> Tuple[IntegerLiteral, int]:
        token, offset = self._token(offset, [TokenType.INTEGER])

        integer = IntegerLiteral(
            value=int(token.value),
            file=token.file,
            line=token.line,
            column=token.column,
        )

        return integer, offset

    def _parse_literal(
        self, offset: int
    ) -> Tuple[BooleanLiteral | StringLiteral | IntegerLiteral, int]:
        token = self._peek_token(offset)

        if not token:
            raise EndOfFileException(self.file)

        if token.type in [TokenType.TRUE, TokenType.FALSE]:
            return self._parse_boolean(offset)

        if token.type == TokenType.STRING:
            return self._parse_string(offset)

        if token.type == TokenType.INTEGER:
            return self._parse_integer(offset)

        expected_types = [
            TokenType.TRUE,
            TokenType.FALSE,
            TokenType.STRING,
            TokenType.INTEGER,
        ]

        raise ParserException(
            file=token.file,
            line=token.line,
            column=token.column,
            expected_token_types=expected_types,
            found_token_type=token.type,
        )

    def _parse_function_call(self, offset: int) -> Tuple[FunctionName, int]:
        token: Optional[Token]
        identifier, offset = self._parse_identifier(offset)

        type_params: List[TypeLiteral] = []
        struct_name: Optional[Identifier] = None
        func_name: Identifier

        token = self._peek_token(offset)

        if token and token.type == TokenType.TYPE_PARAM_BEGIN:
            func_name = identifier
            type_params, offset = self._parse_type_params(offset)
        elif token and token.type == TokenType.COLON:
            _, offset = self._token(offset, [TokenType.COLON])
            struct_name = identifier
            func_name, offset = self._parse_identifier(offset)
        else:
            func_name = identifier

        func_call = FunctionName(
            struct_name=struct_name,
            type_params=type_params,
            func_name=func_name,
            file=self.file,
            line=identifier.line,
            column=identifier.column,
        )

        return func_call, offset

    def _parse_branch(self, offset: int) -> Tuple[Branch, int]:
        if_token, offset = self._token(offset, [TokenType.IF])
        condition, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.BEGIN])
        if_body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.END])

        token = self._peek_token(offset)

        if token and token.type == TokenType.ELSE:
            _, offset = self._token(offset, [TokenType.ELSE])
            _, offset = self._token(offset, [TokenType.BEGIN])
            else_body, offset = self._parse_function_body(offset)
            _, offset = self._token(offset, [TokenType.END])
        else:
            else_body = FunctionBody(line=-1, column=-1, items=[], file=self.file)

        branch = Branch(
            line=if_token.line,
            column=if_token.column,
            condition=condition,
            if_body=if_body,
            else_body=else_body,
            file=self.file,
        )

        return branch, offset

    def _parse_loop(self, offset: int) -> Tuple[Loop, int]:
        while_token, offset = self._token(offset, [TokenType.WHILE])
        condition, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.BEGIN])
        body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.END])

        loop = Loop(
            condition=condition,
            body=body,
            file=while_token.file,
            line=while_token.line,
            column=while_token.column,
        )

        return loop, offset

    def _parse_struct_field_query(self, offset: int) -> Tuple[StructFieldQuery, int]:
        field_name, offset = self._parse_string(offset)
        _, offset = self._token(offset, [TokenType.GET_FIELD])

        field_query = StructFieldQuery(
            field_name=field_name,
            file=field_name.file,
            line=field_name.line,
            column=field_name.column,
        )

        return field_query, offset

    def _parse_struct_field_update(self, offset: int) -> Tuple[StructFieldUpdate, int]:
        field_name, offset = self._parse_string(offset)
        _, offset = self._token(offset, [TokenType.BEGIN])
        new_value_expr, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.END])
        _, offset = self._token(offset, [TokenType.SET_FIELD])

        field_update = StructFieldUpdate(
            field_name=field_name,
            new_value_expr=new_value_expr,
            file=field_name.file,
            line=field_name.line,
            column=field_name.column,
        )

        return field_update, offset

    def _parse_function_body_item(self, offset: int) -> Tuple[FunctionBodyItem, int]:
        token = self._peek_token(offset)

        if not token:
            raise EndOfFileException(self.file)

        # TODO consider inlining _parse_literal in this function
        literal_token_types = [
            TokenType.TRUE,
            TokenType.FALSE,
            TokenType.INTEGER,
            TokenType.STRING,
        ]

        if token.type == TokenType.STRING:
            try:
                return self._parse_struct_field_query(offset)
            except ParserBaseException:
                pass

            try:
                return self._parse_struct_field_update(offset)
            except ParserBaseException:
                pass

        if token.type in literal_token_types:
            return self._parse_literal(offset)
        if token.type == TokenType.IDENTIFIER:
            return self._parse_function_call(offset)
        if token.type == TokenType.IF:
            return self._parse_branch(offset)
        if token.type == TokenType.WHILE:
            return self._parse_loop(offset)

        raise ParserException(
            file=token.file,
            line=token.line,
            column=token.column,
            expected_token_types=literal_token_types
            + [TokenType.IDENTIFIER, TokenType.IF, TokenType.WHILE],
            found_token_type=token.type,
        )

    def _parse_function_body(self, offset: int) -> Tuple[FunctionBody, int]:
        items: List[FunctionBodyItem] = []

        item, offset = self._parse_function_body_item(offset)
        items.append(item)

        while True:
            try:
                item, offset = self._parse_function_body_item(offset)
            except ParserBaseException:
                break

            items.append(item)

        function_body = FunctionBody(
            items=items, file=items[0].file, line=items[0].line, column=items[0].column
        )

        return function_body, offset

    def _parse_function_definition(self, offset: int) -> Tuple[Function, int]:
        function, offset = self._parse_function_declaration(offset)
        _, offset = self._token(offset, [TokenType.BEGIN])
        body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.END])

        function.body = body
        return function, offset

    def _parse_regular_file_root(self, offset: int) -> Tuple[ParsedFile, int]:

        first_token = self._peek_token(offset)

        if first_token:
            first_line = first_token.line
            first_column = first_token.column
        else:
            first_line = 1
            first_column = 1

        functions: List[Function] = []
        structs: List[Struct] = []
        imports: List[Import] = []

        while True:
            try:
                function, offset = self._parse_function_definition(offset)
            except ParserBaseException:
                pass
            else:
                functions.append(function)
                continue

            try:
                struct, offset = self._parse_struct_definition(offset)
            except ParserBaseException:
                pass
            else:
                structs.append(struct)
                continue

            try:
                import_, offset = self._parse_import_statement(offset)
            except ParserBaseException:
                pass
            else:
                imports.append(import_)
                continue

            break

        parsed_file = ParsedFile(
            line=first_line,
            column=first_column,
            functions=functions,
            imports=imports,
            structs=structs,
            types=[],
            file=self.file,
        )

        return parsed_file, offset

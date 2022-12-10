from pathlib import Path
from typing import List, Optional, Tuple

from aaa.parser.exceptions import (
    NewParserEndOfFileException,
    NewParserException,
    ParserBaseException,
)
from aaa.parser.models import (
    Argument,
    Function,
    FunctionBody,
    FunctionName,
    Identifier,
    ParsedFile,
    Struct,
    TypeLiteral,
)
from aaa.tokenizer.models import Token, TokenType


class SingleFileParser:
    def __init__(self, file: Path, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.file = file

    def _peek_token(self, offset: int) -> Optional[Token]:
        try:
            return self.tokens[offset]
        except IndexError:
            return None

    def _token(
        self, offset: int, expected_token_types: List[TokenType]
    ) -> Tuple[Token, int]:
        token = self._peek_token(offset)

        if not token:
            raise NewParserEndOfFileException(file=self.file)

        if token.type not in expected_token_types:
            raise NewParserException(
                file=token.file,
                line=token.line,
                column=token.column,
                expected_token_types=expected_token_types,
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

    # TODO string
    # TODO import_item
    # TODO import_items
    # TODO import_statement

    # TODO boolean
    # TODO integer
    # TODO literal
    # TODO function_call
    # TODO branch
    # TODO loop
    # TODO struct_field_query
    # TODO struct_field_update

    # TODO function_body_item
    # TODO function_body
    # TODO function_definition

    # TODO regular_file_root

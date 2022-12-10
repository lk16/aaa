from pathlib import Path
from typing import List, Optional, Tuple

from aaa.parser.exceptions import (
    NewParserEndOfFileException,
    NewParserException,
    ParserBaseException,
)
from aaa.parser.models import FunctionName, Identifier, TypeLiteral
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

        while True:
            identifier, offset = self._parse_identifier(offset)
            identifiers.append(identifier)

            token, offset = self._token(
                offset, [TokenType.TYPE_PARAM_END, TokenType.COMMA]
            )

            if token.type == TokenType.TYPE_PARAM_END:
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

        while True:
            type_param, offset = self._parse_type_literal(offset)
            type_params.append(type_param)

            token, offset = self._token(
                offset, [TokenType.TYPE_PARAM_END, TokenType.COMMA]
            )

            if token.type == TokenType.TYPE_PARAM_END:
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

    # TODO argument
    # TODO arguments
    # TODO return_types
    # TODO function_declaration
    # TODO builtins_file_root

    # TODO ...
    # TODO regular_file_root

from pathlib import Path
from typing import List, Tuple

from aaa.parser.exceptions import (
    NewParserEndOfFileException,
    NewParserException,
    ParserBaseException,
)
from aaa.parser.models import Identifier, TypeLiteral
from aaa.tokenizer.models import Token, TokenType


class SingleFileParser:
    def __init__(self, file: Path, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.file = file

    def _token(
        self, offset: int, expected_token_types: List[TokenType]
    ) -> Tuple[Token, int]:
        try:
            token = self.tokens[offset]
        except IndexError as e:
            raise NewParserEndOfFileException(file=self.file) from e

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

        identifier, offset = self._parse_identifier(offset)
        identifiers.append(identifier)

        while True:
            token, offset = self._token(
                offset, [TokenType.TYPE_PARAM_END, TokenType.COMMA]
            )

            if token.type == TokenType.TYPE_PARAM_END:
                break

            identifier, offset = self._parse_identifier(offset)
            identifiers.append(identifier)

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

    # TODO type_declaration

    # TODO ...
    # TODO function_declaration
    # TODO builtins_file_root

    # TODO ...
    # TODO regular_file_root

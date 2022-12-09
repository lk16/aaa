from typing import List, Tuple

from aaa.parser.exceptions import NewParserException
from aaa.parser.models import Identifier
from aaa.tokenizer.models import Token, TokenType


class SingleFileParser:
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens

    def _expect(self, offset: int, token_types: List[TokenType]) -> None:
        token = self.tokens[offset]

        if token.type not in token_types:
            raise NewParserException(
                file=token.file,
                line=token.line,
                column=token.column,
                expected_token_types=token_types,
                found_token_type=token.type,
            )

    def _parse_identifier(self, offset: int) -> Tuple[int, Identifier]:
        self._expect(offset, [TokenType.IDENTIFIER])

        token = self.tokens[offset]
        offset += 1

        return offset, Identifier(
            name=token.value, file=token.file, line=token.line, column=token.column
        )

    # TODO identifier
    # TODO flat_type_params
    # TODO flat_type_literal
    # TODO type_declaration

    # TODO ...
    # TODO function_declaration
    # TODO builtins_file_root

    # TODO ...
    # TODO regular_file_root

from pathlib import Path
from typing import Dict, List, Tuple

from aaa.parser.exceptions import ParserBaseException
from aaa.parser.models import Function, ParsedFile, ParserOutput, TypeLiteral
from aaa.parser.tokenizer import Token, Tokenizer, TokenType


class NewParser:
    def __init__(
        self,
        entrypoint: Path,
        builtins_path: Path,
    ) -> None:
        self.entrypoint = entrypoint.resolve()
        self.builtins_path = builtins_path

        self.parsed: Dict[Path, ParsedFile] = {}
        self.parse_queue = [self.entrypoint]
        self.exceptions: List[ParserBaseException] = []

    def run(self) -> ParserOutput:
        self.parsed[self.builtins_path] = self._parse_builtins(self.builtins_path)

        # TODO tokenize and parse entrypoint, enqueue dependencies

        return ParserOutput(
            parsed=self.parsed,
            entrypoint=self.entrypoint,
            builtins_path=self.builtins_path,
        )

    def _expect_token(
        self, tokens: List[Token], offset: int, token_type: TokenType
    ) -> Token:
        if tokens[offset].type != token_type:
            # TODO unexpected token
            raise NotImplementedError

        return tokens[offset]

    def _parse_builtins(self, file: Path) -> ParsedFile:

        functions: List[Function] = []
        types: List[TypeLiteral] = []

        tokens = Tokenizer(file).run()

        offset = 0

        while offset < len(tokens):
            token = tokens[offset]

            if token.type == TokenType.TYPE:
                type, offset = self._parse_type_literal(tokens, offset + 1)
                types.append(type)

            elif token.type == TokenType.FUNCTION:
                function, offset = self._parse_function_declaration(tokens, offset + 1)
                functions.append(function)

            else:
                # TODO unexpected TokenType
                raise NotImplementedError

        return ParsedFile(
            functions=functions,
            imports=[],
            structs=[],
            types=types,
            file=file,
            token=None,  # type: ignore  # TODO
        )

    def _parse_type_literal(
        self, tokens: List[Token], offset: int
    ) -> Tuple[TypeLiteral, int]:

        # TODO
        identifier = self._expect_token(tokens, offset, TokenType.IDENTIFIER)
        offset += 1

        _ = identifier

        if tokens[offset].type == TokenType.TYPE_PARAM_BEGIN:
            ...

        raise NotImplementedError

    def _parse_function_declaration(
        self, tokens: List[Token], offset: int
    ) -> Tuple[Function, int]:
        # TODO
        raise NotImplementedError

from pathlib import Path
from typing import Callable, List, Optional, Tuple

from aaa.parser.lib.exceptions import (
    ChoiceParserException,
    EndOfFile,
    ParserBaseException,
    UnexpectedTokenType,
)
from aaa.parser.lib.models import InnerNode, Token


class BaseParser:
    def _resolve_node_parsers(self, resolver: Callable[[str], "BaseParser"]) -> None:
        pass

    def _print(
        self, tokens: List[Token], offset: int, verbose: bool, parser_name: str
    ) -> None:
        if not verbose:
            return

        if tokens:
            file = str(tokens[0].position.file)
        else:
            file = "<unknown>"

        try:
            token_type = tokens[offset].type
        except IndexError:
            token_type = "<offset is too large>"

        print(f"{file} | offset={offset} | type={token_type} | {parser_name}")

    def parse(
        self, tokens: List[Token], offset: int, verbose: bool = False
    ) -> Tuple[Token | InnerNode | None, int]:
        # Implemented in subclasses.
        raise NotImplementedError


class TokenParser(BaseParser):
    def __init__(self, token_type: str) -> None:
        self.token_type = token_type

    def __repr__(self) -> str:
        return self.token_type

    def parse(
        self, tokens: List[Token], offset: int, verbose: bool = False
    ) -> Tuple[Token | InnerNode | None, int]:
        self._print(tokens, offset, verbose, f"TokenParser for {self.token_type}")

        try:
            token = tokens[offset]
        except IndexError:
            if not tokens:
                file = Path("/dev/unknown")
            else:
                file = tokens[0].position.file

            raise EndOfFile(file, offset, self.token_type)

        if token.type != self.token_type:
            raise UnexpectedTokenType(offset, token, self.token_type)

        return token, offset + 1


class NodeParser(BaseParser):
    def __init__(self, node_type: str) -> None:
        self.node_type = node_type
        self.inner: Optional[BaseParser] = None

    def __repr__(self) -> str:
        return self.node_type

    def _resolve_node_parsers(self, resolver: Callable[[str], "BaseParser"]) -> None:
        self.inner = resolver(self.node_type)

    def parse(
        self, tokens: List[Token], offset: int, verbose: bool = False
    ) -> Tuple[Token | InnerNode | None, int]:
        self._print(tokens, offset, verbose, f"NodeParser for {self.node_type}")

        assert self.inner
        return self.inner.parse(tokens, offset, verbose=verbose)


class ConcatenateParser(BaseParser):
    def __init__(
        self, parsers: List[BaseParser], node_type: Optional[str] = None
    ) -> None:
        self.parsers: List[BaseParser] = []
        self.node_type = node_type

        # Flattening logic
        for parser in parsers:
            if isinstance(parser, ConcatenateParser):
                self.parsers += parser.parsers
            else:
                self.parsers.append(parser)

    def __repr__(self) -> str:
        return "(" + " ".join(repr(parser) for parser in self.parsers) + ")"

    def _resolve_node_parsers(self, resolver: Callable[[str], "BaseParser"]) -> None:
        for parser in self.parsers:
            parser._resolve_node_parsers(resolver)

    def parse(
        self, tokens: List[Token], offset: int, verbose: bool = False
    ) -> Tuple[InnerNode, int]:
        parser_name = "ConcatenateParser"
        if self.node_type is not None:
            parser_name += f" for {self.node_type}"

        self._print(tokens, offset, verbose, parser_name)

        children: List[Token | InnerNode] = []
        for parser in self.parsers:
            child, offset = parser.parse(tokens, offset, verbose=verbose)
            if child:
                children.append(child)

        return InnerNode(children, type=self.node_type), offset


class ChoiceParser(BaseParser):
    def __init__(self, first: BaseParser, second: BaseParser) -> None:
        self.parsers: List[BaseParser] = []

        # Flattening logic
        if isinstance(first, ChoiceParser):
            self.parsers += first.parsers
        else:
            self.parsers.append(first)

        if isinstance(second, ChoiceParser):
            self.parsers += second.parsers
        else:
            self.parsers.append(second)

    def __repr__(self) -> str:
        return "(" + " | ".join(repr(parser) for parser in self.parsers) + " )"

    def _resolve_node_parsers(self, resolver: Callable[[str], "BaseParser"]) -> None:
        for parser in self.parsers:
            parser._resolve_node_parsers(resolver)

    def parse(
        self, tokens: List[Token], offset: int, verbose: bool = False
    ) -> Tuple[Token | InnerNode | None, int]:
        self._print(
            tokens, offset, verbose, f"ChoiceParser with {len(self.parsers)} choices"
        )

        exceptions: List[ParserBaseException] = []

        for parser in self.parsers:
            try:
                return parser.parse(tokens, offset, verbose=verbose)
            except ParserBaseException as e:
                exceptions.append(e)

        raise ChoiceParserException(exceptions)


class OptionalParser(BaseParser):
    def __init__(self, parser: BaseParser) -> None:
        self.inner = parser

    def __repr__(self) -> str:
        return "(" + repr(self.inner) + ")?"

    def _resolve_node_parsers(self, resolver: Callable[[str], "BaseParser"]) -> None:
        self.inner._resolve_node_parsers(resolver)

    def parse(
        self, tokens: List[Token], offset: int, verbose: bool = False
    ) -> Tuple[Token | InnerNode | None, int]:
        self._print(tokens, offset, verbose, "OptionalParser")

        try:
            return self.inner.parse(tokens, offset, verbose=verbose)
        except ParserBaseException:
            return None, offset


class RepeatParser(BaseParser):
    def __init__(self, parser: BaseParser) -> None:
        self.inner = parser

    def __repr__(self) -> str:
        return "(" + repr(self.inner) + ")*"

    def _resolve_node_parsers(self, resolver: Callable[[str], "BaseParser"]) -> None:
        self.inner._resolve_node_parsers(resolver)

    def parse(
        self, tokens: List[Token], offset: int, verbose: bool = False
    ) -> Tuple[Token | InnerNode | None, int]:
        self._print(tokens, offset, verbose, "RepeatParser")

        children: List[Token | InnerNode] = []

        while True:
            try:
                child, offset = self.inner.parse(tokens, offset, verbose=verbose)
            except ParserBaseException:
                break

            if child:
                children.append(child)

        return InnerNode(children), offset


class RepeatAtLeastOnceParser(BaseParser):
    def __init__(self, parser: BaseParser) -> None:
        self.inner = parser

    def __repr__(self) -> str:
        return "(" + repr(self.inner) + ")*"

    def _resolve_node_parsers(self, resolver: Callable[[str], "BaseParser"]) -> None:
        self.inner._resolve_node_parsers(resolver)

    def parse(
        self, tokens: List[Token], offset: int, verbose: bool = False
    ) -> Tuple[Token | InnerNode | None, int]:
        self._print(tokens, offset, verbose, "RepeatAtLeastOnceParser")

        children: List[Token | InnerNode] = []

        while True:
            try:
                child, offset = self.inner.parse(tokens, offset, verbose=verbose)
            except ParserBaseException as e:
                if len(children) == 0:
                    raise e
                break

            if child:
                children.append(child)

        return InnerNode(children), offset

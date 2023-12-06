from typing import List, Optional, Tuple

from aaa.parser.lib.exceptions import ParseError, ParseErrorCollector
from aaa.parser.lib.models import EndOfFile, InnerNode, ParserInput, Token


class BaseParser:
    def __init__(self) -> None:
        self.error_collector: Optional[ParseErrorCollector] = None

    def register_error(self, error: ParseError) -> None:
        assert self.error_collector
        self.error_collector.register(error)

    def _print(
        self, input: ParserInput, offset: int, verbose: bool, parser_name: str
    ) -> None:
        if not verbose:
            return

        try:
            token_type = input.tokens[offset].type
        except IndexError:
            token_type = "<offset is too large>"

        print(f"{input.file} | offset={offset} | type={token_type} | {parser_name}")

    def parse(
        self, input: ParserInput, offset: int, verbose: bool = False
    ) -> Tuple[Token | InnerNode, int]:
        raise NotImplementedError  # Implemented in subclasses.


class TokenParser(BaseParser):
    def __init__(self, token_type: str) -> None:
        self.token_type = token_type

    def __repr__(self) -> str:
        return self.token_type

    def parse(
        self, input: ParserInput, offset: int, verbose: bool = False
    ) -> Tuple[Token | InnerNode, int]:
        self._print(input, offset, verbose, f"TokenParser for {self.token_type}")

        try:
            token = input.tokens[offset]
        except IndexError:
            e: ParseError = ParseError(offset, EndOfFile(input.file), {self.token_type})
            self.register_error(e)
            raise e

        if token.type != self.token_type:
            e = ParseError(offset, token, {self.token_type})
            self.register_error(e)
            raise e

        return token, offset + 1


class NodeParser(BaseParser):
    def __init__(self, node_type: str) -> None:
        self.node_type = node_type
        self.inner: Optional[BaseParser] = None

    def __repr__(self) -> str:
        return self.node_type

    def parse(
        self, input: ParserInput, offset: int, verbose: bool = False
    ) -> Tuple[Token | InnerNode, int]:
        self._print(input, offset, verbose, f"NodeParser for {self.node_type}")

        assert self.inner
        return self.inner.parse(input, offset, verbose=verbose)


class ConcatenateParser(BaseParser):
    def __init__(
        self,
        parsers: List[BaseParser],
        node_type: Optional[str] = None,
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

    def parse(
        self, input: ParserInput, offset: int, verbose: bool = False
    ) -> Tuple[InnerNode, int]:
        parser_name = "ConcatenateParser"
        if self.node_type is not None:
            parser_name += f" for {self.node_type}"

        self._print(input, offset, verbose, parser_name)

        children: List[Token | InnerNode] = []
        for parser in self.parsers:
            child, offset = parser.parse(input, offset, verbose=verbose)
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

    def parse(
        self, input: ParserInput, offset: int, verbose: bool = False
    ) -> Tuple[Token | InnerNode, int]:
        self._print(
            input, offset, verbose, f"ChoiceParser with {len(self.parsers)} choices"
        )

        last_exception: Optional[ParseError] = None

        for parser in self.parsers:
            try:
                return parser.parse(input, offset, verbose=verbose)
            except ParseError as e:
                self.register_error(e)
                last_exception = e

        assert last_exception
        raise last_exception


class OptionalParser(BaseParser):
    def __init__(self, parser: BaseParser) -> None:
        self.inner = parser

    def __repr__(self) -> str:
        return "(" + repr(self.inner) + ")?"

    def parse(
        self, input: ParserInput, offset: int, verbose: bool = False
    ) -> Tuple[Token | InnerNode, int]:
        self._print(input, offset, verbose, "OptionalParser")

        try:
            return self.inner.parse(input, offset, verbose=verbose)
        except ParseError:
            return InnerNode([]), offset


class RepeatParser(BaseParser):
    def __init__(self, parser: BaseParser, min_repeats: int = 0) -> None:
        self.inner = parser
        self.min_repeats = min_repeats

    def __repr__(self) -> str:
        return "(" + repr(self.inner) + ")*"

    def parse(
        self, input: ParserInput, offset: int, verbose: bool = False
    ) -> Tuple[Token | InnerNode, int]:
        self._print(input, offset, verbose, "RepeatParser")

        children: List[Token | InnerNode] = []

        while True:
            try:
                child, offset = self.inner.parse(input, offset, verbose=verbose)
            except ParseError as e:
                if len(children) < self.min_repeats:
                    raise e
                break

            children.append(child)

        return InnerNode(children), offset

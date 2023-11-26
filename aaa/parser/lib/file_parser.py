from pathlib import Path
from typing import Callable, List, Optional, TypeVar

from aaa.parser.lib.exceptions import TokenizerException, UnexpectedTokenType
from aaa.parser.lib.models import Node, Position, Token
from aaa.parser.lib.syntax_loader import SyntaxLoader

T = TypeVar("T")


class FileParser:
    def __init__(self, syntax_file: Path) -> None:
        syntax_loader = SyntaxLoader(syntax_file.read_text())
        self.node_parsers = syntax_loader.parsers
        self.token_regexes = syntax_loader.tokens
        self.root_node_type = syntax_loader.root_node_type
        self.filtered_token_types = syntax_loader.filtered_tokens
        self.top_level_tokens_per_node_type = (
            syntax_loader.top_level_tokens_per_node_type
        )
        self.token_types = syntax_loader.token_types

    def tokenize_file(
        self, file: Path, filter_token_types: bool = True, verbose: bool = False
    ) -> List[Token]:
        # TODO add verbose param
        file_name = str(file.resolve())
        return self.tokenize_text(
            file.read_text(),
            file_name=file_name,
            filter_token_types=filter_token_types,
            verbose=verbose,
        )

    def tokenize_text(
        self,
        text: str,
        file_name: Optional[str] = None,
        filter_token_types: bool = True,
        verbose: bool = False,
    ) -> List[Token]:
        if file_name is None:
            file_name = "/dev/null"

        offset = 0
        max_token_type_length = max(len(token_type) for token_type in self.token_types)

        tokens: List[Token] = []

        while offset < len(text):
            token: Optional[Token] = None
            position = Position.from_text(file_name, offset, text)

            for token_type, regex in self.token_regexes:
                match = regex.match(text, offset)

                if not match:
                    continue

                end = offset + len(match.group(0))
                token = Token(text[offset:end], token_type, position)
                break

            if not token:
                raise TokenizerException(position)

            if not (filter_token_types and token.type in self.filtered_token_types):
                if verbose:
                    position_expected_max_length = len(str(token.position.file)) + 9
                    print(
                        f"{str(token.position):>{position_expected_max_length}}"
                        + f" |{token.type:>{max_token_type_length}}"
                        + f" |{repr(token.value)}"
                    )

                tokens.append(token)

            offset += len(token.value)

        return tokens

    def parse_file(self, file: Path, node_type: str, verbose: bool = False) -> Node:
        text = file.read_text()
        file_name = str(file.resolve())

        return self.parse_text(text, file_name, node_type=node_type, verbose=verbose)

    def parse_text(
        self,
        text: str,
        file_name: Optional[str] = None,
        *,
        verbose: bool = False,
        node_type: str,
    ) -> Node:
        try:
            parser = self.node_parsers[node_type]
        except KeyError as e:
            raise ValueError(f"Unknown node type {node_type}") from e

        tokens = self.tokenize_text(text, file_name, verbose=verbose)
        root, offset = parser.parse(tokens, 0, verbose=verbose)

        if offset != len(tokens):
            top_level_tokens = self.top_level_tokens_per_node_type[node_type]
            raise UnexpectedTokenType(offset, tokens[offset], top_level_tokens)

        return root.flatten()

    def parse_text_and_transform(
        self,
        text: str,
        file_name: Optional[str] = None,
        verbose: bool = False,
        *,
        node_type: str,
        node_transformer: Callable[[str, List[T | Token]], T],
        token_transformer: Callable[[Token], T | Token],
    ) -> T:
        parse_tree = self.parse_text(
            text, file_name, verbose=verbose, node_type=node_type
        )

        return self._transform_parse_tree(
            parse_tree, node_transformer, token_transformer
        )

    def _transform_parse_tree(
        self,
        node: Node,
        node_transformer: Callable[[str, List[T | Token]], T],
        token_transformer: Callable[[Token], T | Token],
    ) -> T:
        transformed_children: List[T | Token] = []
        for child in node.children:
            if isinstance(child, Token):
                transformed_children.append(token_transformer(child))
            else:
                transformed_children.append(
                    self._transform_parse_tree(
                        child, node_transformer, token_transformer
                    )
                )

        return node_transformer(node.type, transformed_children)

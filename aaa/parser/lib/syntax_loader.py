import itertools
import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from aaa.parser.lib.exceptions import ParseErrorCollector, SyntaxJSONLoadError
from aaa.parser.lib.models import Choice
from aaa.parser.lib.parser import (
    BaseParser,
    ChoiceParser,
    ConcatenateParser,
    NodeParser,
    OptionalParser,
    RepeatParser,
    TokenParser,
)

NODE_TYPE_REGEX = re.compile("[A-Z][A-Z_]*")
TOKEN_TYPE_REGEX = re.compile("[a-z][a-z_]*")

NODE_SEGMENT_REGEXES: List[Tuple[str, re.Pattern[str]]] = [
    ("token", re.compile("[a-z][a-z_]*")),
    ("node", re.compile("[A-Z][A-Z_]*")),
    ("whitespace", re.compile("\\s+")),
    ("group_start", re.compile("\\(")),
    ("group_end", re.compile("\\)")),
    ("or", re.compile("\\|")),
    ("optional", re.compile("\\?")),
    ("repeat", re.compile("\\*")),
    ("repeat_at_least_once", re.compile("\\+")),
]


class SyntaxLoader:
    def _load_json(self, syntax_file_content: str) -> Dict[str, Any]:
        try:
            loaded_json = json.loads(syntax_file_content)
        except FileNotFoundError:
            raise SyntaxJSONLoadError("could not find file")
        except ValueError as e:
            raise SyntaxJSONLoadError(f"parse error: {e}")

        if not isinstance(loaded_json, dict):
            raise SyntaxJSONLoadError("Expected root to be a JSON object")

        return loaded_json

    def _check_json_field_prescence(self, loaded_json: Dict[str, Any]) -> None:
        expected_fields = {
            "filtered_tokens",
            "keyword_tokens",
            "nodes",
            "regular_tokens",
            "root_node",
        }

        found_fields = set(loaded_json.keys())

        missing_fields = expected_fields - found_fields
        unexpected_fields = found_fields - expected_fields

        if unexpected_fields:
            raise SyntaxJSONLoadError(
                "Unexpected fields in JSON root: "
                + ", ".join(sorted(unexpected_fields))
            )

        if missing_fields:
            raise SyntaxJSONLoadError(
                "Missing fields in JSON root: " + ", ".join(sorted(missing_fields))
            )

    def _check_json_field_types(
        self, loaded_json: Dict[str, Any]
    ) -> Tuple[Dict[str, str], Dict[str, str], Set[str], Dict[str, str], str]:
        if not isinstance(loaded_json["keyword_tokens"], dict):
            raise SyntaxJSONLoadError("JSON filtered_tokens is not a dict")

        for item in loaded_json["keyword_tokens"].values():
            if not isinstance(item, str):
                raise SyntaxJSONLoadError(f"JSON filtered_item {item} is not a string")

        if not isinstance(loaded_json["regular_tokens"], dict):
            raise SyntaxJSONLoadError("JSON regular_tokens is not a dict")

        for item in loaded_json["regular_tokens"].values():
            if not isinstance(item, str):
                raise SyntaxJSONLoadError(f"JSON regular_tokens {item} is not a string")

        if not isinstance(loaded_json["filtered_tokens"], list):
            raise SyntaxJSONLoadError("JSON filtered_tokens is not a list")

        for item in loaded_json["filtered_tokens"]:
            if not isinstance(item, str):
                raise SyntaxJSONLoadError(
                    f"each item iin JSON filter_tokens should be a string"
                )

        if not isinstance(loaded_json["nodes"], dict):
            raise SyntaxJSONLoadError("JSON nodes is not a dict")

        for item in loaded_json["nodes"].values():
            if not isinstance(item, str):
                raise SyntaxJSONLoadError(f"JSON nodes {item} is not a string")

        if not isinstance(loaded_json["root_node"], str):
            raise SyntaxJSONLoadError("JSON root_node is not a string")

        return (
            loaded_json["keyword_tokens"],
            loaded_json["regular_tokens"],
            set(loaded_json["filtered_tokens"]),
            loaded_json["nodes"],
            loaded_json["root_node"],
        )

    def _build_tokens_regexes(
        self, keyword_tokens: Dict[str, str], regular_tokens: Dict[str, str]
    ) -> List[Tuple[str, re.Pattern[str]]]:
        tokens_list: List[Tuple[str, re.Pattern[str]]] = []
        token_types: Set[str] = set()

        token_items = itertools.chain(keyword_tokens.items(), regular_tokens.items())

        for token_type, regex in token_items:
            if token_type in token_types:
                raise SyntaxJSONLoadError(f"Duplicate token type {token_type}")

            try:
                pattern = re.compile(regex)
            except re.error:
                raise SyntaxJSONLoadError(
                    f"Failed to compile regex for token type {token_type}"
                )

            token_types.add(token_type)
            tokens_list.append((token_type, pattern))

        return tokens_list

    def _check_values(self) -> None:
        missing_filtered_token_types = self.filtered_tokens - self.token_types

        if missing_filtered_token_types:
            raise SyntaxJSONLoadError(
                f"Unknown filtered token type(s): "
                + ", ".join(sorted(missing_filtered_token_types))
            )

        if self.root_node_type not in self.nodes:
            raise SyntaxJSONLoadError("Root node was not found in nodes.")

        for token_type, _ in self.tokens:
            if not TOKEN_TYPE_REGEX.fullmatch(token_type):
                raise SyntaxJSONLoadError(f"Token {token_type} has wrong formatting")

        for node_type in self.nodes.keys():
            if not NODE_TYPE_REGEX.fullmatch(node_type):
                raise SyntaxJSONLoadError(f"Node {node_type} has wrong formatting")

    def __init__(self, syntax_file_content: str) -> None:
        loaded_json = self._load_json(syntax_file_content)
        self._check_json_field_prescence(loaded_json)

        (
            keyword_tokens,
            regular_tokens,
            self.filtered_tokens,
            self.nodes,
            self.root_node_type,
        ) = self._check_json_field_types(loaded_json)

        self.tokens = self._build_tokens_regexes(keyword_tokens, regular_tokens)

        self.token_types = {item[0] for item in self.tokens}

        self._check_values()

        self.error_collector = ParseErrorCollector()

        self.parsers = self._load_parsers()

    def _load_parsers(self) -> Dict[str, ConcatenateParser]:
        node_parsers: Dict[str, ConcatenateParser] = {}

        for node_type, node_value in self.nodes.items():
            node_parsers[node_type] = self._tokenize_parser_definition(
                node_type, node_value
            )

        def update_parsers(parser: BaseParser) -> None:
            parser.error_collector = self.error_collector

            if isinstance(parser, NodeParser):
                parser.inner = node_parsers[parser.node_type]

            elif isinstance(parser, (ChoiceParser, ConcatenateParser)):
                for child in parser.parsers:
                    update_parsers(child)

            elif isinstance(parser, (OptionalParser, RepeatParser)):
                update_parsers(parser.inner)

        for node_type, parser in node_parsers.items():
            update_parsers(parser)
            parser.node_type = node_type

        return node_parsers

    def _tokenize_parser_definition(
        self, node_type: str, node_value: str
    ) -> ConcatenateParser:
        offset = 0
        segments: List[Tuple[str, str]] = []

        while offset < len(node_value):
            found: Optional[re.Match[str]] = None

            for segment_type, segment_regex in NODE_SEGMENT_REGEXES:
                found = segment_regex.match(node_value, offset)

                if found:
                    if found.start() != offset:
                        found = None
                        continue

                    segments.append((segment_type, found.group(0)))
                    offset += len(found.group(0))
                    break

            if not found:
                raise SyntaxJSONLoadError(
                    f"Could not create parser from definition of node {node_type}, error at offset {offset}."
                )

        segments = [segment for segment in segments if segment[0] != "whitespace"]

        return self._parse_parser_definition(node_type, segments)

    def _parse_parser_definition(
        self, node_type: str, segments: List[Tuple[str, str]]
    ) -> ConcatenateParser:
        for segment_type, segment_value in segments:
            if segment_type == "token" and segment_value not in self.token_types:
                raise SyntaxJSONLoadError(
                    f"In parser definition for node {node_type}: Unknown token type {segment_value}"
                )
            if segment_type == "node" and segment_value not in self.nodes:
                raise SyntaxJSONLoadError(
                    f"In parser definition for node {node_type}: Unknown node type {segment_value}"
                )

        parser_or_choice_list: List[Choice | BaseParser] = []

        offset = 0
        while offset < len(segments):
            segment_type, segment_value = segments[offset]

            if segment_type == "token":
                parser_or_choice_list.append(TokenParser(segment_value))
                offset += 1

            elif segment_type == "node":
                parser_or_choice_list.append(NodeParser(segment_value))
                offset += 1

            elif segment_type == "group_start":
                group_end_offset = self._find_group_end_offset(
                    node_type, segments, offset
                )
                group_inner_segments = segments[offset + 1 : group_end_offset]
                group_parser = self._parse_parser_definition(
                    node_type, group_inner_segments
                )
                parser_or_choice_list.append(group_parser)
                offset = group_end_offset + 1

            elif segment_type == "or":
                # NOTE this is handled below this loop
                parser_or_choice_list.append(Choice())
                offset += 1

            elif segment_type in ["optional", "repeat", "repeat_at_least_once"]:
                try:
                    last_item = parser_or_choice_list.pop()
                except IndexError:
                    raise SyntaxJSONLoadError(
                        f"In parser definition for node {node_type}: Invalid syntax"
                    )

                if isinstance(last_item, Choice):
                    raise SyntaxJSONLoadError(
                        f"In parser definition for node {node_type}: Invalid syntax"
                    )

                if segment_type == "optional":
                    parser_or_choice_list.append(OptionalParser(last_item))
                elif segment_type == "repeat":
                    parser_or_choice_list.append(RepeatParser(last_item))
                elif segment_type == "repeat_at_least_once":
                    parser_or_choice_list.append(RepeatParser(last_item, min_repeats=1))
                else:
                    raise NotImplementedError  # This should never happen

                offset += 1

            elif segment_type == "group_end":
                raise SyntaxJSONLoadError(
                    f"In parser definition for node {node_type}: Invalid syntax"
                )

            elif segment_type == "whitespace":
                raise NotImplementedError  # This should never happen

            else:
                raise NotImplementedError  # Unknown segment type

        return self._handle_resolve_choice(node_type, parser_or_choice_list)

    def _handle_resolve_choice(
        self, node_type: str, parser_or_choice_list: List[BaseParser | Choice]
    ) -> ConcatenateParser:
        children: List[BaseParser] = []
        offset = 0

        while offset < len(parser_or_choice_list):
            item = parser_or_choice_list[offset]

            if isinstance(item, BaseParser):
                children.append(item)
                offset += 1
                continue

            try:
                prev_child = children.pop()
            except IndexError:
                raise SyntaxJSONLoadError(
                    f"In parser definition for node {node_type}: Invalid syntax"
                )

            try:
                next_child = parser_or_choice_list[offset + 1]
            except IndexError:
                raise SyntaxJSONLoadError(
                    f"In parser definition for node {node_type}: Invalid syntax"
                )

            if isinstance(next_child, Choice):
                raise SyntaxJSONLoadError(
                    f"In parser definition for node {node_type}: Invalid syntax"
                )

            children.append(ChoiceParser(prev_child, next_child))
            offset += 2

        if len(children) == 0:
            raise SyntaxJSONLoadError(
                f"In parser definition for node {node_type}: Empty group is not allowed"
            )

        return ConcatenateParser(children)

    def _find_group_end_offset(
        self, node_type: str, segments: List[Tuple[str, str]], group_start_offset: int
    ) -> int:
        group_end_remaining = 1
        offset = group_start_offset + 1

        for offset in range(group_start_offset + 1, len(segments)):
            segment_type = segments[offset][0]

            if segment_type == "group_start":
                group_end_remaining += 1
            elif segment_type == "group_end":
                group_end_remaining -= 1
                if group_end_remaining == 0:
                    return offset

        raise SyntaxJSONLoadError(
            f"In parser definition for node {node_type}: Some brackets don't match"
        )

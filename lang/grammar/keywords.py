from parser.parser import LiteralParser, Parser
from typing import Set

from lang.grammar.parser import SymbolType


def _collect_literals(parser: Parser) -> Set[str]:
    if isinstance(parser, LiteralParser):
        return {parser.literal}

    result = set()

    for child in parser.children:
        result |= _collect_literals(child)

    return result


def get_operator_keywords() -> Set[str]:
    return _collect_literals(SymbolType.OPERATOR)

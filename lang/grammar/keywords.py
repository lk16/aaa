from enum import IntEnum
from parser.parser import LiteralParser, Parser, SymbolParser
from typing import Dict, Set

from lang.grammar.parser import REWRITE_RULES, SymbolType


def _collect_literals(parser: Parser, rewrite_rules: Dict[IntEnum, Parser]) -> Set[str]:
    if isinstance(parser, LiteralParser):
        return {parser.literal}

    if isinstance(parser, SymbolParser):
        return _collect_literals(rewrite_rules[parser.symbol_type], rewrite_rules)

    result = set()

    for child in parser.children:
        result |= _collect_literals(child, rewrite_rules)

    return result


def get_operator_keywords() -> Set[str]:
    operator_rewrite_rules = REWRITE_RULES[SymbolType.OPERATOR]
    return _collect_literals(operator_rewrite_rules, REWRITE_RULES)

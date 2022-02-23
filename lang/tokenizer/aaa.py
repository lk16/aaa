from enum import IntEnum, auto
from typing import Dict, Optional

from lang.tokenizer.generic import Parser, ParseTree, lit, new_tokenize_generic, sym


class SymbolType(IntEnum):
    PROGRAM = auto()
    A = auto()
    B = auto()
    C = auto()
    D = auto()


# Shorthand to keep REWRITE_RULES readable
S = SymbolType

REWRITE_RULES: Dict[IntEnum, Parser] = {
    S.PROGRAM: sym(S.A) | sym(S.B),
    S.A: lit("A"),
    S.B: lit("B"),
}

ROOT_SYMBOL = S.PROGRAM


def new_tokenize(code: str) -> Optional[ParseTree]:  # pragma: nocover
    # NOTE Tests call new_tokenize_generic() directly
    return new_tokenize_generic(REWRITE_RULES, ROOT_SYMBOL, code, SymbolType)

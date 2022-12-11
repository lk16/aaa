from typing import List, Tuple

from aaa.tokenizer.models import TokenType

FIXED_SIZED_TOKENS: List[Tuple[str, TokenType]] = [
    ("!", TokenType.SET_FIELD),
    ("!=", TokenType.IDENTIFIER),
    ("<", TokenType.IDENTIFIER),
    ("<=", TokenType.IDENTIFIER),
    (">", TokenType.IDENTIFIER),
    (">=", TokenType.IDENTIFIER),
]

ONE_CHAR_PREFIXED_SIZED_TOKENS = {
    "-": TokenType.IDENTIFIER,
    ",": TokenType.COMMA,
    "?": TokenType.GET_FIELD,
    ".": TokenType.IDENTIFIER,
    "[": TokenType.TYPE_PARAM_BEGIN,
    "]": TokenType.TYPE_PARAM_END,
    "{": TokenType.BEGIN,
    "}": TokenType.END,
    "*": TokenType.IDENTIFIER,
    "/": TokenType.IDENTIFIER,
    "%": TokenType.IDENTIFIER,
    "+": TokenType.IDENTIFIER,
    "=": TokenType.IDENTIFIER,
    ":": TokenType.COLON,
}

TWO_CHAR_PREFIXED_SIZED_TOKENS = {
    "ar": ("gs", TokenType.ARGS),
    "as": ("", TokenType.AS),
    "el": ("se", TokenType.ELSE),
    "fa": ("lse", TokenType.FALSE),
    "fn": ("", TokenType.FUNCTION),
    "fr": ("om", TokenType.FROM),
    "if": ("", TokenType.IF),
    "im": ("port", TokenType.IMPORT),
    "re": ("turn", TokenType.RETURN),
    "st": ("ruct", TokenType.STRUCT),
    "tr": ("ue", TokenType.TRUE),
    "ty": ("pe", TokenType.TYPE),
    "wh": ("ile", TokenType.WHILE),
}

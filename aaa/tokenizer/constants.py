from typing import List, Tuple

from aaa.tokenizer.models import TokenType

FIXED_SIZED_TOKENS: List[Tuple[str, TokenType]] = [
    ("-", TokenType.IDENTIFIER),
    (",", TokenType.COMMA),
    (":", TokenType.COLON),
    ("!", TokenType.SET_FIELD),
    ("!=", TokenType.IDENTIFIER),
    ("?", TokenType.GET_FIELD),
    (".", TokenType.IDENTIFIER),
    ("[", TokenType.TYPE_PARAM_BEGIN),
    ("]", TokenType.TYPE_PARAM_END),
    ("{", TokenType.BEGIN),
    ("}", TokenType.END),
    ("*", TokenType.IDENTIFIER),
    ("/", TokenType.IDENTIFIER),
    ("%", TokenType.IDENTIFIER),
    ("+", TokenType.IDENTIFIER),
    ("<-", TokenType.ASSIGN),
    ("<", TokenType.IDENTIFIER),
    ("<=", TokenType.IDENTIFIER),
    ("=", TokenType.IDENTIFIER),
    (">", TokenType.IDENTIFIER),
    (">=", TokenType.IDENTIFIER),
    ("args", TokenType.ARGS),
    ("as", TokenType.AS),
    ("case", TokenType.CASE),
    ("const", TokenType.CONST),
    ("else", TokenType.ELSE),
    ("enum", TokenType.ENUM),
    ("false", TokenType.FALSE),
    ("fn", TokenType.FUNCTION),
    ("foreach", TokenType.FOREACH),
    ("from", TokenType.FROM),
    ("if", TokenType.IF),
    ("import", TokenType.IMPORT),
    ("match", TokenType.MATCH),
    ("return", TokenType.RETURN),
    ("struct", TokenType.STRUCT),
    ("true", TokenType.TRUE),
    ("type", TokenType.TYPE),
    ("use", TokenType.USE),
    ("while", TokenType.WHILE),
]

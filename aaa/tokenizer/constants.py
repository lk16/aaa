from typing import List, Tuple

from aaa.tokenizer.models import TokenType

FIXED_SIZED_TOKENS: List[Tuple[str, TokenType]] = [
    # Keep this sorted by length, then by token value
    # 7 chars
    ("default", TokenType.DEFAULT),
    ("foreach", TokenType.FOREACH),
    # 6 chars
    ("import", TokenType.IMPORT),
    ("return", TokenType.RETURN),
    ("struct", TokenType.STRUCT),
    # 5 chars
    ("const", TokenType.CONST),
    ("false", TokenType.FALSE),
    ("match", TokenType.MATCH),
    ("never", TokenType.NEVER),
    ("while", TokenType.WHILE),
    # 4 chars
    ("args", TokenType.ARGS),
    ("case", TokenType.CASE),
    ("else", TokenType.ELSE),
    ("enum", TokenType.ENUM),
    ("from", TokenType.FROM),
    ("true", TokenType.TRUE),
    ("type", TokenType.TYPE),
    # 3 chars
    ("use", TokenType.USE),
    # 2 chars
    ("!=", TokenType.IDENTIFIER),
    ("<-", TokenType.ASSIGN),
    ("<=", TokenType.IDENTIFIER),
    (">=", TokenType.IDENTIFIER),
    ("as", TokenType.AS),
    ("fn", TokenType.FUNCTION),
    ("if", TokenType.IF),
    # 1 char
    ("!", TokenType.SET_FIELD),
    ("%", TokenType.IDENTIFIER),
    ("*", TokenType.IDENTIFIER),
    ("+", TokenType.IDENTIFIER),
    (",", TokenType.COMMA),
    ("-", TokenType.IDENTIFIER),
    (".", TokenType.IDENTIFIER),
    ("/", TokenType.IDENTIFIER),
    (":", TokenType.COLON),
    ("<", TokenType.IDENTIFIER),
    ("=", TokenType.IDENTIFIER),
    (">", TokenType.IDENTIFIER),
    ("?", TokenType.GET_FIELD),
    ("[", TokenType.TYPE_PARAM_BEGIN),
    ("]", TokenType.TYPE_PARAM_END),
    ("{", TokenType.BEGIN),
    ("}", TokenType.END),
]

from enum import Enum

from aaa import Position


class TokenType(Enum):
    ARGS = "ARGS"
    AS = "AS"
    ASSIGN = "ASSIGN"
    BEGIN = "BEGIN"
    COLON = "COLON"
    COMMA = "COMMA"
    COMMENT = "COMMENT"
    CONST = "CONST"
    ELSE = "ELSE"
    END = "END"
    FALSE = "FALSE"
    FOREACH = "FOREACH"
    FROM = "FROM"
    FUNCTION = "FUNCTION"
    GET_FIELD = "GET_FIELD"
    IDENTIFIER = "IDENTIFIER"
    IF = "IF"
    IMPORT = "IMPORT"
    INTEGER = "INTEGER"
    RETURN = "RETURN"
    SET_FIELD = "SET_FIELD"
    STRING = "STRING"
    STRUCT = "STRUCT"
    TRUE = "TRUE"  # replace TRUE and FALSE with BOOLEAN
    TYPE = "TYPE"
    TYPE_PARAM_BEGIN = "TYPE_PARAM_BEGIN"
    TYPE_PARAM_END = "TYPE_PARAM_END"
    USE = "USE"
    WHILE = "WHILE"
    WHITESPACE = "WHITESPACE"


class Token:
    def __init__(self, position: Position, type: TokenType, value: str) -> None:
        self.position = position
        self.type = type
        self.value = value

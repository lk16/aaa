from enum import Enum

from aaa import Position


class TokenType(Enum):
    ARGS = "ARGS"
    AS = "AS"
    ASSIGN = "ASSIGN"
    BLOCK_START = "BLOCK_START"
    CASE = "CASE"
    CALL = "CALL"
    CHARACTER = "CHARACTER"
    COLON = "COLON"
    COMMA = "COMMA"
    COMMENT = "COMMENT"
    CONST = "CONST"
    DEFAULT = "DEFAULT"
    ELSE = "ELSE"
    BLOCK_END = "BLOCK_END"
    ENUM = "ENUM"
    FALSE = "FALSE"
    FOREACH = "FOREACH"
    FROM = "FROM"
    FUNCTION = "FUNCTION"
    GET_FIELD = "GET_FIELD"
    IDENTIFIER = "IDENTIFIER"
    IF = "IF"
    IMPORT = "IMPORT"
    INTEGER = "INTEGER"
    MATCH = "MATCH"
    NEVER = "NEVER"
    RETURN = "RETURN"
    SET_FIELD = "SET_FIELD"
    STRING = "STRING"
    STRUCT = "STRUCT"
    TRUE = "TRUE"  # replace TRUE and FALSE with BOOLEAN
    TYPE = "TYPE"
    SQUARE_BRACKET_OPEN = "SQUARE_BRACKET_OPEN"
    SQUARE_BRACKET_CLOSE = "SQUARE_BRACKET_CLOSE"
    USE = "USE"
    WHILE = "WHILE"
    WHITESPACE = "WHITESPACE"


class Token:
    def __init__(self, position: Position, type: TokenType, value: str) -> None:
        self.position = position
        self.type = type
        self.value = value

    def __repr__(self) -> str:
        return repr(self.value)

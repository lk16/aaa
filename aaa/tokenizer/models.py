from enum import Enum
from pathlib import Path


class TokenType(Enum):
    ARGS = "ARGS"
    AS = "AS"
    BEGIN = "BEGIN"
    COMMA = "COMMA"
    COLON = "COLON"
    COMMENT = "COMMENT"
    ELSE = "ELSE"
    END = "END"
    FALSE = "FALSE"
    FROM = "FROM"
    FUNCTION = "FUNCTION"
    GET_FIELD = "GET_FIELD"
    IDENTIFIER = "IDENTIFIER"
    IF = "IF"
    INTEGER = "INTEGER"
    IMPORT = "IMPORT"
    RETURN = "RETURN"
    SET_FIELD = "SET_FIELD"
    SHEBANG = "SHEBANG"
    STRING = "STRING"
    STRUCT = "STRUCT"
    TRUE = "TRUE"  # replace TRUE and FALSE with BOOLEAN
    TYPE = "TYPE"
    TYPE_PARAM_BEGIN = "TYPE_PARAM_BEGIN"
    TYPE_PARAM_END = "TYPE_PARAM_END"
    WHILE = "WHILE"
    WHITESPACE = "WHITESPACE"


class Token:
    def __init__(self, type: TokenType, value: str) -> None:
        self.type = type
        self.value = value
        self.file: Path
        self.line = -1
        self.column = -1

    def set_location(self, file: Path, line: int, column: int) -> None:
        self.file = file
        self.line = line
        self.column = column

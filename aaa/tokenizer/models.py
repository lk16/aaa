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
    OPERATOR = "OPERATOR"
    RETURN = "RETURN"
    SET_FIELD = "SET_FIELD"
    SHEBANG = "SHEBANG"
    STRING = "STRING"
    STRUCT = "STRUCT"
    TRUE = "TRUE"
    TYPE = "TYPE"
    TYPE_PARAM_BEGIN = "TYPE_PARAM_BEGIN"
    TYPE_PARAM_END = "TYPE_PARAM_END"
    WHILE = "WHILE"
    WHITESPACE = "WHITESPACE"


class Token:
    def __init__(
        self, type: TokenType, value: str, file: Path, line: int, column: int
    ) -> None:
        self.type = type
        self.value = value
        self.file = file
        self.line = line
        self.column = column

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.type}, value={repr(self.value)})"

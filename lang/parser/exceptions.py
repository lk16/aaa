from enum import IntEnum
from typing import List, Optional


class InternalParseError(Exception):
    def __init__(self, offset: int, symbol_type: Optional[IntEnum]) -> None:
        self.offset = offset
        self.symbol_type = symbol_type
        super().__init__()


class ParseError(Exception):
    def __init__(
        self,
        line_number: int,
        column_number: int,
        line: str,
        expected_symbol_types: List[IntEnum],
    ) -> None:
        self.line_number = line_number
        self.column_number = column_number
        self.line = line
        self.expected_symbol_types = expected_symbol_types

        # TODO make this show some human readable parse error message
        super().__init__()

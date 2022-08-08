from pathlib import Path
from typing import Dict

from lark.lexer import Token

from lang.models import AaaModel
from lang.models.parse import BuiltinFunction


class ProgramImport(AaaModel):
    token: Token
    imported_name: str
    original_name: str
    source_file: Path

    def identify(self) -> str:
        return self.imported_name


class Builtins(AaaModel):
    functions: Dict[str, BuiltinFunction]

    @classmethod
    def empty(cls) -> "Builtins":
        return Builtins(functions={})

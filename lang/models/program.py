from pathlib import Path

from lark.lexer import Token

from lang.models import AaaModel


class ProgramImport(AaaModel):
    token: Token
    imported_name: str
    original_name: str
    source_file: Path

    def identify(self) -> str:
        return self.imported_name

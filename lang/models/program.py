from pathlib import Path

from lang.models import AaaModel


class ProgramImport(AaaModel):
    original_name: str
    source_file: Path

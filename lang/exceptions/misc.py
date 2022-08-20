from pathlib import Path

from lang.exceptions import AaaException


class MainFunctionNotFound(AaaException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f"{self.file}: No main function found"

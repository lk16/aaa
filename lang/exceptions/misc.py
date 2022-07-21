from pathlib import Path

from lark.exceptions import UnexpectedInput

from lang.exceptions import AaaLoadException


class MainFunctionNotFound(AaaLoadException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f"{self.file}: No main function found"


class MissingEnvironmentVariable(AaaLoadException):
    def __init__(self, env_var_name: str) -> None:
        self.env_var_name = env_var_name

    def __str__(self) -> str:
        return f"Required environment variable {self.env_var_name} was not set."


class AaaParseException(AaaLoadException):
    def __init__(self, *, file: Path, parse_error: UnexpectedInput) -> None:
        self.parse_error = parse_error
        self.file = file

    def where(self) -> str:
        return f"{self.file}:{self.parse_error.line}:{self.parse_error.column}"

    def __str__(self) -> str:
        context = self.parse_error.get_context(self.file.read_text())

        return f"{self.where()}: Could not parse file\n" + context

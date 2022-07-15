from pathlib import Path

from lark.exceptions import UnexpectedInput

from lang.exceptions import AaaLoadException


class MainFunctionNotFound(AaaLoadException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:  # pragma: nocover
        return f"No main function found in {self.file}"


class MissingEnvironmentVariable(AaaLoadException):
    def __init__(self, env_var_name: str) -> None:
        self.env_var_name = env_var_name

    def __str__(self) -> str:  # pragma: nocover
        return f"Required environment variable {self.env_var_name} was not set."


class AaaParseException(AaaLoadException):
    def __init__(self, cause: UnexpectedInput) -> None:
        self.cause = cause

    def __str__(self) -> str:
        return str(self.cause)

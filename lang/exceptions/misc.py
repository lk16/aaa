from pathlib import Path

from lang.exceptions import AaaLoadException


# TODO needs better baseclass
class MainFunctionNotFound(AaaLoadException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:  # pragma: nocover
        return f"No main function found in {self.file}"


# TODO needs better baseclass
class MissingEnvironmentVariable(AaaLoadException):
    def __init__(self, env_var_name: str) -> None:
        self.env_var_name = env_var_name

    def __str__(self) -> str:  # pragma: nocover
        return f"Required environment variable {self.env_var_name} was not set."

import os
import secrets
from pathlib import Path
from tempfile import gettempdir
from typing import Optional


class AaaModel:
    def __repr__(self) -> str:  # pragma: nocover
        return (
            f"{type(self).__qualname__}("
            + ", ".join(
                f"{field_name}: {repr(field)}"
                for field_name, field in vars(self).items()
            )
            + ")"
        )


class Position:
    def __init__(self, file: Path, line: int, column: int) -> None:
        self.file = file
        self.line = line
        self.column = column

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"

    def __hash__(self) -> int:
        return hash((self.file, self.line, self.column))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Position):
            return False

        return str(self) == str(other)

    def context(self) -> str:  # pragma: nocover
        code = self.file.read_text()
        line = code.split("\n")[self.line - 1]
        return line + "\n" + ((self.column - 1) * " ") + "^\n"

    def short_filename(self) -> str:  # pragma: nocover
        try:
            short = self.file.relative_to(Path.cwd())
        except ValueError:
            # It is possible the file is not in the subpath of cwd
            # We just print the absolute path then
            short = self.file

        return str(short)

    def __lt__(self, other: "Position") -> bool:
        return (self.file, self.line, self.column) < (
            other.file,
            other.line,
            other.column,
        )

    def __repr__(self) -> str:
        return str(self)


class AaaException(Exception):
    ...


class AaaEnvironmentError(AaaException):
    ...


def get_stdlib_path() -> Path:
    try:
        stdlib_folder = os.environ["AAA_STDLIB_PATH"]
    except KeyError as e:
        raise AaaEnvironmentError(
            "Environment variable AAA_STDLIB_PATH is not set.\n"
            + "Cannot find standard library!"
        ) from e

    return Path(stdlib_folder) / "builtins.aaa"


AAA_DEFAULT_OUTPUT_FOLDER_ROOT = Path(gettempdir()) / "aaa/transpiled"
AAA_TEST_OUTPUT_FOLDER_ROOT = Path(gettempdir()) / "aaa/transpiled/tests"


def __create_output_folder(root: Path, name: Optional[str]) -> Path:
    if name is None:
        name = "".join(secrets.choice("0123456789abcdef") for _ in range(16))

    path = root / name
    path.resolve().mkdir(exist_ok=True, parents=True)
    return path


def create_test_output_folder(name: Optional[str] = None) -> Path:
    return __create_output_folder(AAA_TEST_OUTPUT_FOLDER_ROOT, name)


def create_output_folder(name: Optional[str] = None) -> Path:
    return __create_output_folder(AAA_DEFAULT_OUTPUT_FOLDER_ROOT, name)


def aaa_project_root() -> Path:
    return (Path(__file__).parent / "..").resolve()

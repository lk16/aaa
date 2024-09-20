import os
import secrets
from pathlib import Path
from tempfile import gettempdir


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


class AaaException(Exception):
    ...


class AaaEnvironmentError(AaaException):
    ...


AAA_DEFAULT_OUTPUT_FOLDER_ROOT = Path(gettempdir()) / "aaa/transpiled"


def __create_output_folder(root: Path, name: str | None) -> Path:
    if name is None:
        name = "".join(secrets.choice("0123456789abcdef") for _ in range(16))

    path = root / name
    path.resolve().mkdir(exist_ok=True, parents=True)
    return path


def create_output_folder(name: str | None = None) -> Path:
    return __create_output_folder(AAA_DEFAULT_OUTPUT_FOLDER_ROOT, name)


def aaa_project_root() -> Path:
    return (Path(__file__).parent / "..").resolve()


def get_builtins_path() -> Path:
    return get_stdlib_path() / "builtins.aaa"


def get_stdlib_path() -> Path:
    try:
        return Path(os.environ["AAA_STDLIB_PATH"])
    except KeyError as e:
        raise AaaEnvironmentError(
            "Cannot find builtins, because env var AAA_STDLIB_PATH is not set.\n"
        ) from e

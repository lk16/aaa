from pathlib import Path
from typing import List

from lang.exceptions import AaaLoadException


class ImportException(AaaLoadException):
    ...


class AbsoluteImportError(ImportException):
    def __init__(
        self,
        *,
        file: Path,
    ) -> None:
        self.file = file

    def __str__(self) -> str:  # pragma: nocover
        return f"In {self.file}: absolute imports are forbidden"


class ImportedItemNotFound(ImportException):
    def __init__(
        self,
        *,
        file: Path,
        import_source: str,
        imported_item: str,
    ) -> None:
        self.imported_item = imported_item
        self.import_source = import_source
        self.file = file

    def __str__(self) -> str:  # pragma: nocover
        return (
            f'In {self.file}: could not import "'
            + '{self.imported_item}" from {self.import_source}\n'
        )


class FileReadError(ImportException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:  # pragma: nocover
        return f'Failed to open or read "{self.file}". Maybe it doesn\'t exist?\n'


class CyclicImportError(ImportException):
    def __init__(self, *, dependencies: List[Path], failed_import: Path) -> None:
        self.dependencies = dependencies
        self.failed_import = failed_import

    def __str__(self) -> str:  # pragma: nocover
        msg = "Cyclic import dependency was detected:\n"
        msg += f"           {self.failed_import}\n"

        cycle_start = self.dependencies.index(self.failed_import)
        for cycle_item in reversed(self.dependencies[cycle_start + 1 :]):
            msg += f"depends on {cycle_item}\n"

        msg += f"depends on {self.failed_import}\n"

        return msg


class ImportNamingCollision(ImportException):
    ...  # TODO

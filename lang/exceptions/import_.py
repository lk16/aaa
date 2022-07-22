from pathlib import Path
from typing import List

from lang.exceptions import AaaLoadException, error_location
from lang.models.parse import Import


class ImportException(AaaLoadException):
    ...


class AbsoluteImportError(ImportException):
    def __init__(
        self,
        *,
        file: Path,
        import_: Import,
    ) -> None:
        self.file = file
        self.import_ = import_

    def where(self) -> str:
        return error_location(self.file, self.import_.token)

    def __str__(self) -> str:
        return f"{self.where()}: absolute imports are forbidden"


class ImportedItemNotFound(ImportException):
    def __init__(
        self,
        *,
        file: Path,
        import_: Import,
        imported_item: str,
    ) -> None:
        self.import_ = import_
        self.imported_item = imported_item
        self.file = file

    def __str__(self) -> str:
        return (
            f"{self.file}: Could not import "
            + f'"{self.imported_item}" from {self.import_.source}\n'
        )


class FileReadError(ImportException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f"{self.file}: Failed to open or read\n"


class CyclicImportError(ImportException):
    def __init__(self, *, dependencies: List[Path], failed_import: Path) -> None:
        self.dependencies = dependencies
        self.failed_import = failed_import

    def __str__(self) -> str:
        msg = "Cyclic import dependency was detected:\n"
        msg += f"           {self.failed_import}\n"

        cycle_start = self.dependencies.index(self.failed_import)
        for cycle_item in reversed(self.dependencies[cycle_start + 1 :]):
            msg += f"depends on {cycle_item}\n"

        msg += f"depends on {self.failed_import}\n"

        return msg

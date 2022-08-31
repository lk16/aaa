from pathlib import Path

from lang.cross_referencer.models import Import
from lang.exceptions import AaaException, error_location


class CrossReferenceBaseException(AaaException):
    ...


class ImportedItemNotFound(CrossReferenceBaseException):
    def __init__(
        self,
        *,
        file: Path,
        import_: Import,
    ) -> None:
        self.import_ = import_
        self.file = file

    def where(self) -> str:
        return error_location(self.file, self.import_.parsed.token)

    def __str__(self) -> str:
        return (
            f"{self.where()}: Could not import "
            + f"{self.import_.source_name} from {self.import_.source_file}\n"
        )


class IndirectImportException(CrossReferenceBaseException):
    def __init__(
        self,
        *,
        file: Path,
        import_: Import,
    ) -> None:
        self.file = file
        self.import_ = import_

    def where(self) -> str:
        return error_location(self.file, self.import_.parsed.token)

    def __str__(self) -> str:
        return f"{self.where()}: Indirect imports are forbidden.\n"

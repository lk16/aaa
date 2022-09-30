from pathlib import Path

from lark.lexer import Token

from aaa import AaaException, error_location
from aaa.cross_referencer.models import Function, Identifiable, Import, Type


class CrossReferenceBaseException(AaaException):
    # TODO move file and token fields here

    def describe(self, item: Identifiable) -> str:
        if isinstance(item, Function):
            return f"function {item.name}"
        elif isinstance(item, Import):
            return f"imported object {item.name}"
        elif isinstance(item, Type):
            return f"type {item.name}"
        else:  # pragma: nocover
            assert False


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
        return error_location(self.file, self.import_.token)

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
        return error_location(self.file, self.import_.token)

    def __str__(self) -> str:
        return f"{self.where()}: Indirect imports are forbidden.\n"


class CollidingIdentifier(CrossReferenceBaseException):
    def __init__(
        self,
        *,
        file: Path,
        colliding: Identifiable,
        found: Identifiable,
    ) -> None:
        self.colliding = colliding
        self.found = found
        self.file = file

    def where(self, item: Identifiable) -> str:
        return error_location(self.file, item.token)

    def __str__(self) -> str:
        lhs_where = self.where(self.colliding)
        rhs_where = self.where(self.found)

        return (
            f"{lhs_where}: {self.describe(self.colliding)} collides with:\n"
            f"{rhs_where}: {self.describe(self.found)}\n"
        )


class UnknownIdentifier(CrossReferenceBaseException):
    def __init__(self, *, file: Path, name: str, token: Token) -> None:
        self.name = name
        self.token = token
        self.file = file

    def where(self) -> str:
        return error_location(self.file, self.token)

    def __str__(self) -> str:
        return f"{self.where()}: Usage of unknown identifier {self.name}\n"


class InvalidTypeParameter(CrossReferenceBaseException):
    def __init__(self, *, file: Path, identifiable: Identifiable) -> None:
        self.file = file
        self.identifiable = identifiable

    def where(self) -> str:
        return error_location(self.file, self.identifiable.token)

    def __str__(self) -> str:
        return f"{self.where()}: Cannot use {self.describe(self.identifiable)} as type parameter\n"


class InvalidType(CrossReferenceBaseException):
    def __init__(self, *, file: Path, identifiable: Identifiable) -> None:
        self.file = file
        self.identifiable = identifiable

    def where(self) -> str:
        return error_location(self.file, self.identifiable.token)

    def __str__(self) -> str:
        return (
            f"{self.where()}: Cannot use {self.describe(self.identifiable)} as type\n"
        )


class MainFunctionNotFound(CrossReferenceBaseException):
    ...  # TODO implement and use

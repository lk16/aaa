from pathlib import Path

from aaa import AaaException, error_location
from aaa.cross_referencer.models import (
    ArgumentIdentifiable,
    Function,
    Identifiable,
    Import,
    Type,
    Unresolved,
)
from aaa.parser.models import TypeLiteral


class CrossReferenceBaseException(AaaException):
    # TODO move file and token fields here

    def describe(self, item: Identifiable) -> str:
        if isinstance(item, Function):
            return f"function {item.name}"
        elif isinstance(item, Import):
            if isinstance(item.source, Unresolved):
                return f"imported identifier {item.imported_name}"

            return self.describe(item.source)
        elif isinstance(item, Type):
            return f"type {item.name}"
        elif isinstance(item, ArgumentIdentifiable):
            return f"function argument {item.name}"
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
        return error_location(self.file, self.import_.line, self.import_.column)

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
        return error_location(self.file, self.import_.line, self.import_.column)

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

    def __str__(self) -> str:
        lhs_where = error_location(
            self.file, self.colliding.line, self.colliding.column
        )
        rhs_where = error_location(self.file, self.found.line, self.found.column)

        return (
            f"{lhs_where}: {self.describe(self.colliding)} collides with:\n"
            f"{rhs_where}: {self.describe(self.found)}\n"
        )


class UnknownIdentifier(CrossReferenceBaseException):
    def __init__(self, *, file: Path, name: str, line: int, column: int) -> None:
        self.name = name
        self.line = line
        self.column = column
        self.file = file

    def where(self) -> str:
        return error_location(self.file, self.line, self.column)

    def __str__(self) -> str:
        return f"{self.where()}: Usage of unknown identifier {self.name}\n"


class InvalidTypeParameter(CrossReferenceBaseException):
    def __init__(self, *, file: Path, identifiable: Identifiable) -> None:
        self.file = file
        self.identifiable = identifiable

    def where(self) -> str:
        return error_location(
            self.file, self.identifiable.line, self.identifiable.column
        )

    def __str__(self) -> str:
        return f"{self.where()}: Cannot use {self.describe(self.identifiable)} as type parameter\n"


class InvalidArgument(CrossReferenceBaseException):
    def __init__(self, *, used: TypeLiteral, found: Identifiable) -> None:
        self.used = used
        self.found = found

    def __str__(self) -> str:
        used_loc = error_location(self.used.file, self.used.line, self.used.column)
        found_loc = error_location(self.found.file, self.found.line, self.found.column)

        return (
            f"{used_loc}: Cannot use {self.used.identifier.name} as argument\n"
            + f"{found_loc}: {self.describe(self.found)} collides\n"
        )


class InvalidType(CrossReferenceBaseException):
    def __init__(self, *, file: Path, identifiable: Identifiable) -> None:
        self.file = file
        self.identifiable = identifiable

    def where(self) -> str:
        return error_location(
            self.file, self.identifiable.line, self.identifiable.column
        )

    def __str__(self) -> str:
        return (
            f"{self.where()}: Cannot use {self.describe(self.identifiable)} as type\n"
        )


class MainFunctionNotFound(CrossReferenceBaseException):
    def __init__(self, file: Path) -> None:
        self.file = file
        super().__init__()

    def __str__(self) -> str:
        return f"{self.file}: No main function found"


class MainIsNotAFunction(CrossReferenceBaseException):
    def __init__(self, file: Path, identifiable: Identifiable) -> None:
        self.file = file
        self.identifiable = identifiable
        super().__init__()

    def __str__(self) -> str:
        return f"{self.file}: Found {self.describe(self.identifiable)} instead of function main"


class UnexpectedTypeParameterCount(CrossReferenceBaseException):
    def __init__(
        self,
        file: Path,
        line: int,
        column: int,
        expected_param_count: int,
        found_param_count: int,
    ) -> None:
        self.file = file
        self.line = line
        self.column = column
        self.expected_param_count = expected_param_count
        self.found_param_count = found_param_count

    def where(self) -> str:
        return error_location(self.file, self.line, self.column)

    def __str__(self) -> str:
        return (
            f"{self.where()}: Unexpected number of type parameters\n"
            + f"Expected parameter count: {self.expected_param_count}\n"
            + f"   Found parameter count: {self.found_param_count}"
        )


class KeywordUsedAsIdentifier(CrossReferenceBaseException):
    def __init__(self, *, line: int, column: int, file: Path, keyword: str) -> None:
        self.line = line
        self.column = column
        self.file = file
        self.keyword = keyword

    def where(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"

    def __str__(self) -> str:
        return f'{self.where()}: Can\'t use keyword "{self.keyword}" as identifier.'

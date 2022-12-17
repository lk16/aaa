from pathlib import Path

from aaa import AaaException, Position
from aaa.cross_referencer.models import (
    ArgumentIdentifiable,
    Function,
    Identifiable,
    Import,
    UnresolvedImport,
    UnresolvedType,
)
from aaa.parser.models import TypeLiteral


class CrossReferenceBaseException(AaaException):
    def describe(self, item: Identifiable) -> str:
        if isinstance(item, Function):
            return f"function {item.name}"
        elif isinstance(item, Import):
            return self.describe(item.source)
        elif isinstance(item, UnresolvedImport):
            return f"imported identifier {item.name}"
        elif isinstance(item, UnresolvedType):
            return f"type {item.name}"
        elif isinstance(item, ArgumentIdentifiable):
            return f"function argument {item.name}"
        else:  # pragma: nocover
            assert False


class ImportedItemNotFound(CrossReferenceBaseException):
    def __init__(self, import_: UnresolvedImport) -> None:
        self.import_ = import_

    def __str__(self) -> str:
        return (
            f"{self.import_.position}: Could not import "
            + f"{self.import_.source_name} from {self.import_.source_file}\n"
        )


class IndirectImportException(CrossReferenceBaseException):
    def __init__(self, import_: UnresolvedImport) -> None:
        self.import_ = import_

    def __str__(self) -> str:
        return f"{self.import_.position}: Indirect imports are forbidden.\n"


class CollidingIdentifier(CrossReferenceBaseException):
    def __init__(self, colliding: Identifiable, found: Identifiable) -> None:
        self.colliding = colliding
        self.found = found

    def __str__(self) -> str:
        return (
            f"{self.colliding.position}: {self.describe(self.colliding)} collides with:\n"
            f"{self.found.position}: {self.describe(self.found)}\n"
        )


class UnknownIdentifier(CrossReferenceBaseException):
    def __init__(self, position: Position, name: str) -> None:
        self.position = position
        self.name = name

    def __str__(self) -> str:
        return f"{self.position}: Usage of unknown identifier {self.name}\n"


class InvalidTypeParameter(CrossReferenceBaseException):
    def __init__(self, identifiable: Identifiable) -> None:
        self.identifiable = identifiable

    def __str__(self) -> str:
        return f"{self.identifiable.position}: Cannot use {self.describe(self.identifiable)} as type parameter\n"


class InvalidArgument(CrossReferenceBaseException):
    def __init__(self, used: TypeLiteral, found: Identifiable) -> None:
        self.used = used
        self.found = found

    def __str__(self) -> str:
        return (
            f"{self.used.position}: Cannot use {self.used.identifier.name} as argument\n"
            + f"{self.found.position}: {self.describe(self.found)} collides\n"
        )


class InvalidType(CrossReferenceBaseException):
    def __init__(self, identifiable: Identifiable) -> None:
        self.identifiable = identifiable

    def __str__(self) -> str:
        return f"{self.identifiable.position}: Cannot use {self.describe(self.identifiable)} as type\n"


class MainFunctionNotFound(CrossReferenceBaseException):
    def __init__(self, file: Path) -> None:
        self.file = file
        super().__init__()

    def __str__(self) -> str:
        return f"{self.file}: No main function found"


class MainIsNotAFunction(CrossReferenceBaseException):
    def __init__(self, identifiable: Identifiable) -> None:
        self.identifiable = identifiable
        super().__init__()

    def __str__(self) -> str:
        return f"{self.identifiable.position}: Found {self.describe(self.identifiable)} instead of function main"


class UnexpectedTypeParameterCount(CrossReferenceBaseException):
    def __init__(
        self,
        position: Position,
        expected_param_count: int,
        found_param_count: int,
    ) -> None:
        self.position = position
        self.expected_param_count = expected_param_count
        self.found_param_count = found_param_count

    def __str__(self) -> str:
        return (
            f"{self.position}: Unexpected number of type parameters\n"
            + f"Expected parameter count: {self.expected_param_count}\n"
            + f"   Found parameter count: {self.found_param_count}"
        )

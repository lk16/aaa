from pathlib import Path
from typing import List, Tuple

import aaa.parser.models as parser
from aaa import AaaException, Position
from aaa.cross_referencer.models import (
    AaaCrossReferenceModel,
    Argument,
    Function,
    Identifiable,
    Import,
    Type,
    Variable,
)
from aaa.parser.models import TypeLiteral


def describe(item: Identifiable | Argument | Variable) -> str:
    if isinstance(item, Function):
        return f"function {item.name}"
    elif isinstance(item, Import):
        return f"imported identifier {item.name}"
    elif isinstance(item, Type):
        return f"type {item.name}"
    elif isinstance(item, Argument):
        return f"function argument {item.name}"
    elif isinstance(item, Variable):
        return f"local variable {item.name}"
    else:  # pragma: nocover
        assert False


class CrossReferenceBaseException(AaaException):
    ...


class ImportedItemNotFound(CrossReferenceBaseException):
    def __init__(self, import_: Import) -> None:
        self.import_ = import_

    def __str__(self) -> str:
        return (
            f"{self.import_.position}: Could not import "
            + f"{self.import_.source_name} from {self.import_.source_file}\n"
        )


class IndirectImportException(CrossReferenceBaseException):
    def __init__(self, import_: Import) -> None:
        self.import_ = import_

    def __str__(self) -> str:
        return f"{self.import_.position}: Indirect imports are forbidden.\n"


class CollidingIdentifier(CrossReferenceBaseException):
    def __init__(self, colliding: List[Identifiable | Argument | Variable]) -> None:
        assert len(colliding) == 2
        assert colliding[0].position.file == colliding[1].position.file

        def sort_key(item: AaaCrossReferenceModel) -> Tuple[int, int]:
            return (item.position.line, item.position.column)

        self.colliding = sorted(colliding, key=sort_key)

    def __str__(self) -> str:
        msg = "Found name collision:\n"

        for item in self.colliding:
            msg += f"{item.position}: {describe(item)}\n"

        return msg


class CollidingEnumVariant(CrossReferenceBaseException):
    def __init__(self, enum: parser.Enum, variants: List[parser.EnumVariant]) -> None:
        assert len(variants) == 2
        assert variants[0].position.file == variants[1].position.file

        def sort_key(item: parser.EnumVariant) -> Tuple[int, int]:
            return (item.position.line, item.position.column)

        self.colliding = sorted(variants, key=sort_key)
        self.enum = enum

    def __str__(self) -> str:
        msg = "Duplicate enum variant name collision:\n"

        for item in self.colliding:
            msg += f"{item.position}: enum variant {self.enum.identifier.name}:{item.name.name}\n"

        return msg


class UnknownIdentifier(CrossReferenceBaseException):
    def __init__(self, position: Position, name: str) -> None:
        self.position = position
        self.name = name

    def __str__(self) -> str:
        return f"{self.position}: Usage of unknown identifier {self.name}\n"


class InvalidReturnType(CrossReferenceBaseException):
    def __init__(self, identifiable: Identifiable) -> None:
        self.identifiable = identifiable

    def __str__(self) -> str:
        return f"{self.identifiable.position}: Cannot use {describe(self.identifiable)} as return type\n"


class InvalidArgument(CrossReferenceBaseException):
    def __init__(self, used: TypeLiteral, found: Identifiable) -> None:
        self.used = used
        self.found = found

    def __str__(self) -> str:
        return (
            f"{self.used.position}: Cannot use {self.used.identifier.name} as argument\n"
            + f"{self.found.position}: {describe(self.found)} collides\n"
        )


class InvalidType(CrossReferenceBaseException):
    def __init__(self, identifiable: Identifiable) -> None:
        self.identifiable = identifiable

    def __str__(self) -> str:
        return f"{self.identifiable.position}: Cannot use {describe(self.identifiable)} as type\n"


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
            + f"   Found parameter count: {self.found_param_count}\n"
        )


class CircularDependencyError(CrossReferenceBaseException):
    def __init__(self, dependencies: List[Path]) -> None:
        self.dependencies = dependencies

    def __str__(self) -> str:
        message = "Circular dependency detected:\n"
        for dep in self.dependencies:
            message += f"- {dep}\n"
        return message


class InvalidEnumType(CrossReferenceBaseException):
    def __init__(self, position: Position, identifiable: Identifiable) -> None:
        self.identifiable = identifiable
        self.position = position

    def __str__(self) -> str:
        return (
            f"{self.position}: Cannot use {describe(self.identifiable)} as enum type\n"
        )


class InvalidEnumVariant(CrossReferenceBaseException):
    def __init__(self, position: Position, enum: Type, variant_name: str) -> None:
        self.enum = enum
        self.variant_name = variant_name
        self.position = position

    def __str__(self) -> str:
        return f"{self.position}: Variant {self.variant_name} of enum {self.enum.name} does not exist\n"

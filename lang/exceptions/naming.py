from pathlib import Path
from typing import Union

from lang.exceptions import NamingException, error_location
from lang.models.parse import (
    Function,
    Identifier,
    ParsedTypePlaceholder,
    Struct,
    TypeLiteral,
)
from lang.models.program import ProgramImport


class CollidingIdentifier(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        colliding: Union[Struct, Function],
        found: Union[Struct, Function, ProgramImport],
    ) -> None:
        self.colliding = colliding
        self.found = found
        self.file = file

    def describe(self, item: Union[Struct, Function, ProgramImport]) -> str:
        if isinstance(item, Struct):
            return f"struct {item.identify()}"
        elif isinstance(item, Function):
            return f"function {item.identify()}"
        elif isinstance(item, ProgramImport):
            return f"imported identifier {item.identify()}"
        else:  # pragma: nocover
            assert False

    def __str__(self) -> str:
        lhs_where = error_location(self.file, self.colliding.token)
        rhs_where = error_location(self.file, self.found.token)

        return (
            f"{lhs_where}: {self.describe(self.colliding)} collides with:\n"
            f"{rhs_where}: {self.describe(self.found)}\n"
        )


class ArgumentNameCollision(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: Function,
    ) -> None:
        self.function = function
        self.file = file

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:
        # TODO add what the actual colliding argument name is
        return f"{self.where()}: Function {self.function.name} has argument which collides with function name another or argument\n"


class UnknownIdentifier(NamingException):
    def __init__(
        self, *, file: Path, function: Function, identifier: Identifier
    ) -> None:
        self.function = function
        self.identifier = identifier
        self.file = file

    def where(self) -> str:
        return error_location(self.file, self.identifier.token)

    def __str__(self) -> str:
        return f"{self.where()}: Function {self.function.name} uses unknown identifier {self.identifier.name}\n"


class UnknownArgumentType(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: Function,
        type_literal: TypeLiteral,
    ) -> None:
        self.function = function
        self.type_literal = type_literal
        self.file = file

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:
        return f"{self.where()}: Function {self.function.name} has argument with unknown type {self.type_literal.type_name}\n"


class UnknownStructField(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: Function,
        struct: Struct,
        field_name: str,
    ) -> None:
        self.function = function
        self.struct = struct
        self.field_name = field_name
        self.file = file

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:
        return f"{self.where()}: Function {self.function.name} tries to use non-existing field {self.field_name} of struct {self.struct.name}\n"


class UnknownPlaceholderType(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: Function,
        placeholder: ParsedTypePlaceholder,
    ) -> None:
        self.function = function
        self.placeholder = placeholder
        self.file = file

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:
        return f"{self.where()}: Function {self.function.name} uses unknown placeholder {self.placeholder.name}\n"

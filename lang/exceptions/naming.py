from pathlib import Path
from typing import Union

from lang.exceptions import NamingException, error_location
from lang.models.parse import (
    Argument,
    BuiltinFunction,
    Function,
    Identifier,
    ParsedType,
    Struct,
)
from lang.models.program import ProgramImport


class CollidingIdentifier(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        colliding: Union[Argument, BuiltinFunction, Function, Struct, ProgramImport],
        found: Union[Argument, BuiltinFunction, Function, Struct, ProgramImport],
    ) -> None:
        self.colliding = colliding
        self.found = found
        self.file = file

    def describe(
        self, item: Union[Argument, BuiltinFunction, Function, Struct, ProgramImport]
    ) -> str:
        if isinstance(item, Struct):
            return f"struct {item.identify()}"
        elif isinstance(item, Function):
            return f"function {item.identify()}"
        elif isinstance(item, BuiltinFunction):
            return f"built-in function {item.identify()}"
        elif isinstance(item, ProgramImport):
            return f"imported identifier {item.identify()}"
        elif isinstance(item, Argument):
            return f"function argument {item.name}"
        else:  # pragma: nocover
            assert False

    def where(
        self, item: Union[Argument, BuiltinFunction, Function, Struct, ProgramImport]
    ) -> str:
        if isinstance(item, Argument):
            return error_location(self.file, item.name_token)
        if isinstance(item, BuiltinFunction):
            return "<stdlib>:"  # TODO
        else:
            return error_location(self.file, item.token)

    def __str__(self) -> str:
        lhs_where = self.where(self.colliding)
        rhs_where = self.where(self.found)

        return (
            f"{lhs_where}: {self.describe(self.colliding)} collides with:\n"
            f"{rhs_where}: {self.describe(self.found)}\n"
        )


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
        parsed_type: ParsedType,
    ) -> None:
        self.function = function
        self.parsed_type = parsed_type
        self.file = file

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:
        return f"{self.where()}: Function {self.function.name} has argument with unknown type {self.parsed_type.name}\n"


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


# TODO consider merging this with UnknownArgumentType
class UnknownPlaceholderType(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: Function,
        parsed_type: ParsedType,
    ) -> None:
        self.function = function
        self.parsed_type = parsed_type
        self.file = file

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:
        return f"{self.where()}: Function {self.function.name} uses unknown placeholder {self.parsed_type.name}\n"

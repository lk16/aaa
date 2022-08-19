from pathlib import Path
from typing import Union

from lang.exceptions import NamingException, error_location
from lang.models.parse import Argument, Function, Identifier, Struct
from lang.models.program import ProgramImport
from lang.models.typing.var_type import VariableType


class CollidingIdentifier(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        colliding: Union[Argument, Function, Struct, ProgramImport],
        found: Union[Argument, Function, Struct, ProgramImport],
    ) -> None:
        self.colliding = colliding
        self.found = found
        self.file = file

    def describe(self, item: Union[Argument, Function, Struct, ProgramImport]) -> str:
        if isinstance(item, Struct):
            return f"struct {item.identify()}"
        elif isinstance(item, Function):
            return f"function {item.identify()}"
        elif isinstance(item, ProgramImport):
            return f"imported identifier {item.identify()}"
        elif isinstance(item, Argument):
            return f"function argument {item.name}"
        else:  # pragma: nocover
            assert False

    def where(self, item: Union[Argument, Function, Struct, ProgramImport]) -> str:
        if isinstance(item, Argument):
            return error_location(self.file, item.name_token)
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
        var_type: VariableType,
    ) -> None:
        self.function = function
        self.var_type = var_type
        self.file = file

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:
        string = f"{self.where()}: Function {self.function.name} "

        if self.var_type.is_placeholder():
            string += "uses unknown placeholder "
        else:
            string += "has argument with unknown type "

        string += f"{self.var_type.name}\n"
        return string


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

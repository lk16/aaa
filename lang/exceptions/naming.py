from pathlib import Path
from typing import Union

from lang.exceptions import AaaLoadException, error_location
from lang.models.parse import Function, Struct


class NamingException(AaaLoadException):
    def __init__(self, *, file: Path) -> None:
        self.file = file


# TODO support colliding import
class IdentifierCollision(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        colliding: Union[Struct, Function],
    ) -> None:
        self.colliding = colliding
        super().__init__(file=file)

    def __str__(self) -> str:  # pragma: nocover
        lhs_where = error_location(self.file, self.colliding.token)
        # TODO point out what we collide with

        if isinstance(self.colliding, Struct):
            lhs = f"Struct {self.colliding.name}"
        elif isinstance(self.colliding, Function):
            lhs = f"Function {self.colliding.name}"

        return f"{lhs_where}: {lhs} collides with other identifier.\n"


class ArgumentNameCollision(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: Function,
    ) -> None:
        self.function = function
        super().__init__(file=file)

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:  # pragma: nocover
        return f"{self.where()}: Function {self.function.name} has argument which collides with function name another or argument\n"


# TODO rename to UnknownIdentifier
class UnknownFunction(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: Function,
    ) -> None:
        self.function = function
        super().__init__(file=file)

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:  # pragma: nocover
        # TODO add name of unknown identifier
        return (
            f"{self.where()}: Function {self.function.name} uses unknown identifier\n"
        )


# TODO add name of unknown type, consider merging with Unknown identifier
class UnknownType(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: Function,
    ) -> None:
        self.function = function
        super().__init__(file=file)

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:  # pragma: nocover
        return f"{self.where()}: Function {self.function.name} uses unknown type\n"


# TODO add name of unknown struct field
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
        super().__init__(file=file)

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:  # pragma: nocover
        return f"{self.where()}: Function {self.function.name} tries to use non-existing field {self.field_name} of struct {self.struct.name}\n"


# TODO add name of unknown placeholder type
class UnknownPlaceholderType(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: Function,
    ) -> None:
        self.function = function
        super().__init__(file=file)

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:  # pragma: nocover
        return (
            f"{self.where()}: Function {self.function.name} uses unknown placeholder\n"
        )

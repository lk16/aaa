from pathlib import Path
from typing import Union

from lang.exceptions import AaaLoadException, error_location
from lang.models.parse import Function, Struct
from lang.models.program import ProgramImport


class NamingException(AaaLoadException):
    def __init__(self, *, file: Path) -> None:  # TODO refactor this out
        self.file = file


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
        super().__init__(file=file)

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
        super().__init__(file=file)

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:
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

    def __str__(self) -> str:
        # TODO add name of unknown identifier
        return (
            f"{self.where()}: Function {self.function.name} uses unknown identifier\n"
        )


# TODO add name of unknown type, consider merging with UnknownIdentifier
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

    def __str__(self) -> str:
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

    def __str__(self) -> str:
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

    def __str__(self) -> str:
        return (
            f"{self.where()}: Function {self.function.name} uses unknown placeholder\n"
        )

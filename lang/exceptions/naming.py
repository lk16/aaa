from pathlib import Path

from lang.exceptions import AaaLoadException, error_location
from lang.models.parse import Function, Struct


class NamingException(AaaLoadException):
    def __init__(self, *, file: Path) -> None:
        self.file = file


# TODO create IdentifierCollision replacing FunctionNameCollision and StructNameCollision
class FunctionNameCollision(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file)

    def __str__(self) -> str:  # pragma: nocover
        return f"Function {self.function.name} collides with other identifier.\n"


class StructNameCollision(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        struct: "Struct",
    ) -> None:
        self.struct = struct
        super().__init__(file=file)

    def __str__(self) -> str:  # pragma: nocover
        return f"Struct {self.struct.name} collides with other identifier.\n"


class ArgumentNameCollision(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file)

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:  # pragma: nocover
        return f"{self.where()}: Function {self.function.name} uses argument which collides with function name another or argument\n"


# TODO rename to UnknownIdentifier
class UnknownFunction(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file)

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:  # pragma: nocover
        return (
            f"{self.where()}: Function {self.function.name} uses unknown identifier\n"
        )


class UnknownType(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file)

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:  # pragma: nocover
        return f"{self.where()}: Function {self.function.name} uses unknown type\n"


class UnknownStructField(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
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


class UnknownPlaceholderType(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file)

    def where(self) -> str:
        return error_location(self.file, self.function.token)

    def __str__(self) -> str:  # pragma: nocover
        return (
            f"{self.where()}: Function {self.function.name} uses unknown placeholder\n"
        )

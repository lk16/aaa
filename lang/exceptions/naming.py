from pathlib import Path
from typing import Sequence

from lang.exceptions import AaaLoadException
from lang.parse.models import AaaTreeNode, Function, Struct
from lang.typing.types import TypePlaceholder, VariableType


class NamingException(AaaLoadException):
    def __init__(self, *, file: Path, node: "AaaTreeNode") -> None:
        self.file = file
        self.node = node
        self.code = file.read_text()
        return super().__init__()

    def __str__(self) -> str:  # pragma: nocover
        return "TypeErrorException message, override me!"

    def get_error_header(self) -> str:
        return ""

    # TODO rename this function
    def format_typestack(
        self, type_stack: Sequence[VariableType | TypePlaceholder]
    ) -> str:  # pragma: nocover
        return " ".join(repr(type_stack_item) for type_stack_item in type_stack)


class FunctionNameCollision(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file, node=function)

    def __str__(self) -> str:
        return (
            f"Function {self.function.name} collides with other identifier.\n"
            + self.get_error_header()
        )


class StructNameCollision(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        struct: "Struct",
    ) -> None:
        self.struct = struct
        super().__init__(file=file, node=struct)

    def __str__(self) -> str:
        return (
            f"Struct {self.struct.name} collides with other identifier.\n"
            + self.get_error_header()
        )


class ArgumentNameCollision(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        node: "AaaTreeNode",
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file, node=node)

    def __str__(self) -> str:
        return (
            f"Argument name already used by other argument or function name in {self.function.name}\n"
            + self.get_error_header()
        )


class UnknownFunction(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        node: "AaaTreeNode",
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file, node=node)

    def __str__(self) -> str:
        return (
            f"Unknown function or identifier in {self.function.name}\n"
            + self.get_error_header()
        )


class UnknownType(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        node: "AaaTreeNode",
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file, node=node)

    def __str__(self) -> str:
        return f"Unknown type in {self.function.name}\n" + self.get_error_header()


class UnknownStructField(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        node: "AaaTreeNode",
        function: "Function",
        struct: Struct,
        field_name: str,
    ) -> None:
        self.function = function
        self.struct = struct
        self.field_name = field_name
        super().__init__(file=file, node=node)

    def __str__(self) -> str:
        return (
            f"Usage of unknown field in {self.function.name}: struct {self.struct.name} has no field {self.field_name}\n"
            + self.get_error_header()
        )


class UnknownPlaceholderType(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        node: "AaaTreeNode",
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file, node=node)

    def __str__(self) -> str:
        return (
            f"Usage of unknown placeholder type in {self.function.name}\n"
            + self.get_error_header()
        )

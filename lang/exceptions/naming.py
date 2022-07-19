from pathlib import Path

from lang.exceptions import AaaLoadException
from lang.models.parse import AaaTreeNode, Function, Struct


class NamingException(AaaLoadException):
    def __init__(self, *, file: Path, node: "AaaTreeNode") -> None:
        self.file = file
        self.node = node
        self.code = file.read_text()
        return super().__init__()

    def __str__(self) -> str:  # pragma: nocover
        return "TypeErrorException message, override me!"


class FunctionNameCollision(NamingException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file, node=function)

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
        super().__init__(file=file, node=struct)

    def __str__(self) -> str:  # pragma: nocover
        return f"Struct {self.struct.name} collides with other identifier.\n"


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

    def __str__(self) -> str:  # pragma: nocover
        return f"Argument name already used by other argument or function name in {self.function.name}\n"


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

    def __str__(self) -> str:  # pragma: nocover
        return f"Unknown function or identifier in {self.function.name}\n"


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

    def __str__(self) -> str:  # pragma: nocover
        return f"Unknown type in {self.function.name}\n"


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

    def __str__(self) -> str:  # pragma: nocover
        return f"Usage of unknown field in {self.function.name}: struct {self.struct.name} has no field {self.field_name}\n"


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

    def __str__(self) -> str:  # pragma: nocover
        return f"Usage of unknown placeholder type in {self.function.name}\n"

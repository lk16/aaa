from parser.tokenizer.models import Token
from pathlib import Path
from typing import TYPE_CHECKING, List, Sequence, Tuple

from lang.runtime.parse import Struct

if TYPE_CHECKING:  # pragma: nocover
    from lang.runtime.parse import AaaTreeNode, Function

from lang.typing.types import Signature, TypePlaceholder, TypeStack, VariableType


class TypeException(Exception):
    def __init__(self, *, file: Path, tokens: List[Token], node: "AaaTreeNode") -> None:
        self.file = file
        self.tokens = tokens
        self.node = node
        self.code = file.read_text()
        return super().__init__()

    def __str__(self) -> str:  # pragma: nocover
        return "TypeErrorException message, override me!"

    def get_line_column_numbers(self) -> Tuple[int, int]:
        offset = self.tokens[self.node.token_offset].offset
        before_offset = self.code[:offset]
        line_num = 1 + before_offset.count("\n")
        prev_newline_offset = before_offset.rfind("\n")
        col_num = offset - prev_newline_offset
        return line_num, col_num

    def get_line(self) -> str:
        offset = self.tokens[self.node.token_offset].offset
        prev_newline = self.code.rfind("\n", 0, offset)

        next_newline = self.code.find("\n", offset)
        if next_newline == -1:
            next_newline = len(self.code)

        return self.code[prev_newline + 1 : next_newline]

    def get_error_header(self) -> str:
        line_no, col_no = self.get_line_column_numbers()
        line = self.get_line()
        return (
            f"{self.file}:{line_no}:{col_no}\n"
            + f"{line}\n"
            + " " * (col_no - 1)
            + "^\n"
        )

    # TODO rename this function
    def format_typestack(
        self, type_stack: Sequence[VariableType | TypePlaceholder]
    ) -> str:  # pragma: nocover
        return " ".join(repr(type_stack_item) for type_stack_item in type_stack)


class FunctionTypeError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        function: "Function",
        expected_return_types: List[VariableType | TypePlaceholder],
        computed_return_types: TypeStack,
    ) -> None:
        self.function = function
        self.expected_return_types = expected_return_types
        self.computed_return_types = computed_return_types
        super().__init__(file=file, tokens=tokens, node=function)

    def __str__(self) -> str:
        return (
            f"Function {self.function.name} returns wrong type(s)\n"
            + self.get_error_header()
            + "expected return types: "
            + self.format_typestack(self.expected_return_types)
            + "\n"
            + "   found return types: "
            + self.format_typestack(self.computed_return_types)
            + "\n"
        )


class StackUnderflowError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        node: "AaaTreeNode",
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file, tokens=tokens, node=node)

    def __str__(self) -> str:
        return (
            f"Stack underflow inside {self.function.name}\n" + self.get_error_header()
        )


class StackTypesError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        node: "AaaTreeNode",
        function: "Function",
        signature: Signature,
        type_stack: TypeStack,
    ) -> None:
        self.function = function
        self.signature = signature
        self.type_stack = type_stack
        super().__init__(file=file, tokens=tokens, node=node)

    def __str__(self) -> str:
        return (
            f"Invalid stack types inside {self.function.name}\n"
            + self.get_error_header()
            + "  Type stack: "
            + self.format_typestack(self.type_stack)
            + "\n"
            "Expected top: " + self.format_typestack(self.signature.arg_types) + "\n"
        )


class ConditionTypeError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        node: "AaaTreeNode",
        function: "Function",
        type_stack: TypeStack,
        condition_stack: TypeStack,
    ) -> None:
        self.function = function
        self.type_stack = type_stack
        self.condition_stack = condition_stack
        super().__init__(file=file, tokens=tokens, node=node)

    def __str__(self) -> str:
        return (
            f"Invalid stack modification in condition inside {self.function.name}\n"
            + self.get_error_header()
            + "stack before: "
            + self.format_typestack(self.type_stack)
            + "\n"
            + " stack after: "
            + self.format_typestack(self.condition_stack)
            + "\n"
        )


class BranchTypeError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        node: "AaaTreeNode",
        function: "Function",
        type_stack: TypeStack,
        if_stack: TypeStack,
        else_stack: TypeStack,
    ) -> None:
        self.function = function
        self.type_stack = type_stack
        self.if_stack = if_stack
        self.else_stack = else_stack
        super().__init__(file=file, tokens=tokens, node=node)

    def __str__(self) -> str:
        return (
            f"Inconsistent stack modification in if (else)-block {self.function.name}\n"
            + self.get_error_header()
            + "           before: "
            + self.format_typestack(self.type_stack)
            + "\n"
            + "  after if-branch: "
            + self.format_typestack(self.if_stack)
            + "\n"
            + "after else-branch: "
            + self.format_typestack(self.else_stack)
            + "\n"
        )


class LoopTypeError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        node: "AaaTreeNode",
        function: "Function",
        type_stack: TypeStack,
        loop_stack: TypeStack,
    ) -> None:
        self.function = function
        self.type_stack = type_stack
        self.loop_stack = loop_stack
        super().__init__(file=file, tokens=tokens, node=node)

    def __str__(self) -> str:
        return (
            f"Stack modification inside loop body inside {self.function.name}\n"
            + self.get_error_header()
            + "before loop: "
            + self.format_typestack(self.type_stack)
            + "\n"
            + " after loop: "
            + self.format_typestack(self.loop_stack)
            + "\n"
        )


class FunctionNameCollision(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file, tokens=tokens, node=function)

    def __str__(self) -> str:
        return (
            f"Function {self.function.name} was already defined.\n"
            + self.get_error_header()
        )


class ArgumentNameCollision(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        node: "AaaTreeNode",
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file, tokens=tokens, node=node)

    def __str__(self) -> str:
        return (
            f"Argument name already used by other argument or function name in {self.function.name}\n"
            + self.get_error_header()
        )


class UnknownFunction(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        node: "AaaTreeNode",
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file, tokens=tokens, node=node)

    def __str__(self) -> str:
        return (
            f"Unknown function or identifier in {self.function.name}\n"
            + self.get_error_header()
        )


class UnknownType(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        node: "AaaTreeNode",
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file, tokens=tokens, node=node)

    def __str__(self) -> str:
        return f"Unknown type in {self.function.name}\n" + self.get_error_header()


class UnknownStructField(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        node: "AaaTreeNode",
        function: "Function",
        struct: Struct,
        field_name: str,
    ) -> None:
        self.function = function
        self.struct = struct
        self.field_name = field_name
        super().__init__(file=file, tokens=tokens, node=node)

    def __str__(self) -> str:
        return (
            f"Usage of unknown field in {self.function.name}: struct {self.struct.name} has no field {self.field_name}\n"
            + self.get_error_header()
        )


class UnknownPlaceholderType(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        node: "AaaTreeNode",
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file, tokens=tokens, node=node)

    def __str__(self) -> str:
        return (
            f"Usage of unknown placeholder type in {self.function.name}\n"
            + self.get_error_header()
        )


class InvalidMainSignuture(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        node: "AaaTreeNode",
        function: "Function",
    ) -> None:
        self.function = function
        super().__init__(file=file, tokens=tokens, node=node)

    def __str__(self) -> str:
        return f"Invalid signature for main function\n" + self.get_error_header()


# TODO this is not really a type exception
class AbsoluteImportError(TypeException):
    def __str__(self) -> str:
        return f"Absolute imports are not allowed\n" + self.get_error_header()


# TODO this is not really a type exception
class ImportedItemNotFound(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        node: "AaaTreeNode",
        imported_item: str,
    ) -> None:
        self.imported_item = imported_item
        super().__init__(file=file, tokens=tokens, node=node)

    def __str__(self) -> str:
        return (
            f'Imported item "{self.imported_item}" was not found\n'
            + self.get_error_header()
        )


# TODO needs better baseclass
class FileReadError(Exception):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f'Failed to open or read "{self.file}". Maybe it doesn\'t exist?\n'


# TODO needs better baseclass
class CyclicImportError(Exception):
    def __init__(self, *, dependencies: List[Path], failed_import: Path) -> None:
        self.dependencies = dependencies
        self.failed_import = failed_import

    def __str__(self) -> str:
        msg = "Cyclic import dependency was detected:\n"
        _ = msg

        msg += f"           {self.failed_import}\n"

        cycle_start = self.dependencies.index(self.failed_import)
        for cycle_item in reversed(self.dependencies[cycle_start + 1 :]):
            msg += f"depends on {cycle_item}\n"

        msg += f"depends on {self.failed_import}\n"

        return msg


# TODO needs better baseclass
class MainFunctionNotFound(Exception):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f"No main function found in {self.file}"


# TODO needs better baseclass
class MissingEnvironmentVariable(Exception):
    def __init__(self, env_var_name: str) -> None:
        self.env_var_name = env_var_name

    def __str__(self) -> str:
        return f"Required environment variable {self.env_var_name} was not set."


class GetFieldOfNonStructTypeError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        node: "AaaTreeNode",
        function: "Function",
        type_stack: TypeStack,
    ) -> None:
        self.function = function
        self.type_stack = type_stack
        super().__init__(file=file, tokens=tokens, node=node)

    def __str__(self) -> str:
        return (
            f"Attempt to get field of non-struct value in {self.function.name}\n"
            + self.get_error_header()
            + "  Type stack: "
            + self.format_typestack(self.type_stack)
            + "\n"
            "Expected top: <struct type> str \n"
        )


class SetFieldOfNonStructTypeError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        tokens: List[Token],
        node: "AaaTreeNode",
        function: "Function",
        type_stack: TypeStack,
    ) -> None:
        self.function = function
        self.type_stack = type_stack
        super().__init__(file=file, tokens=tokens, node=node)

    def __str__(self) -> str:
        return (
            f"Attempt to set field of non-struct value in {self.function.name}\n"
            + self.get_error_header()
            + "  Type stack: "
            + self.format_typestack(self.type_stack)
            + "\n"
            "Expected top: <struct type> str <new value of field>\n"
        )

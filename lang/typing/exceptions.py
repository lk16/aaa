from parser.tokenizer.models import Token
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from lang.parse import AaaTreeNode, Function

from lang.typing.signatures import PlaceholderType, Signature, TypeStack


class TypeException(Exception):
    def __init__(
        self, file: Path, function: Function, tokens: List[Token], node: "AaaTreeNode"
    ) -> None:
        self.file = file
        self.function = function
        self.tokens = tokens
        self.node = node
        self.code = file.read_text()
        return super().__init__(self.what())

    def what(self) -> str:
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
            f"{self.file}:{line_no}:{col_no}" + f"{line}\n" + " " * (col_no - 1) + "^\n"
        )

    def format_typestack(self, type_stack: TypeStack) -> str:
        formatted: List[str] = []
        for item in type_stack:
            if isinstance(item, PlaceholderType):
                formatted.append(f"*{item.name}")
            else:
                formatted.append(item.__name__)

        return " ".join(formatted)


class FunctionTypeError(TypeException):
    def __init__(
        self,
        file: Path,
        function: "Function",
        tokens: List[Token],
        expected_return_types: TypeStack,
        computed_return_types: TypeStack,
    ) -> None:
        super().__init__(file, function, tokens, function)
        self.expected_return_types = expected_return_types
        self.computed_return_types = computed_return_types

    def what(self) -> str:
        return (
            f"Function type error for {self.function.name}\n"
            + self.get_error_header()
            + "expected return types: "
            + self.format_typestack(self.expected_return_types)
            + "\n"
            + "   found return types: "
            + self.format_typestack(self.computed_return_types)
            + "\n"
        )


class StackUnderflowError(TypeException):
    def what(self) -> str:
        return (
            f"Stack underflow inside {self.function.name}\n" + self.get_error_header()
        )


class StackTypesError(TypeException):
    def __init__(
        self,
        file: Path,
        function: "Function",
        tokens: List[Token],
        node: "AaaTreeNode",
        signature: Signature,
        type_stack: TypeStack,
    ) -> None:
        super().__init__(file, function, tokens, node)
        self.signature = signature
        self.type_stack = type_stack

    def what(self) -> str:
        return (
            f"Stack type error inside {self.function.name}\n"
            + self.get_error_header()
            + "  Type stack: "
            + self.format_typestack(self.type_stack)
            + "\n"
            "Expected top: " + self.format_typestack(self.signature.arg_types) + "\n"
        )


class ConditionTypeError(TypeException):
    ...


class BranchTypeError(TypeException):
    ...


class LoopTypeError(TypeException):
    ...


class FunctionNameCollision(TypeException):
    ...


class ArgumentNameCollision(TypeException):
    ...


class UnknownFunction(TypeException):
    ...


class UnknownType(TypeException):
    ...


class UnknownPlaceholderTypes(TypeException):
    ...

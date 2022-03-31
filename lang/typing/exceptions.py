from parser.tokenizer.models import Token
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:  # pragma: nocover
    from lang.runtime.parse import AaaTreeNode, Function

from lang.typing.signatures import PlaceholderType, Signature, TypeStack


class TypeException(Exception):
    def __init__(
        self, file: Path, function: "Function", tokens: List[Token], node: "AaaTreeNode"
    ) -> None:
        self.file = file
        self.function = function
        self.tokens = tokens
        self.node = node
        self.code = file.read_text()
        return super().__init__(self.what())

    def what(self) -> str:  # pragma: nocover
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

    def format_typestack(self, type_stack: TypeStack) -> str:  # pragma: nocover
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
        self.expected_return_types = expected_return_types
        self.computed_return_types = computed_return_types
        super().__init__(file, function, tokens, function)

    def what(self) -> str:
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
        self.signature = signature
        self.type_stack = type_stack
        super().__init__(file, function, tokens, node)

    def what(self) -> str:
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
        file: Path,
        function: "Function",
        tokens: List[Token],
        node: "AaaTreeNode",
        type_stack: TypeStack,
        condition_stack: TypeStack,
    ) -> None:
        self.type_stack = type_stack
        self.condition_stack = condition_stack
        super().__init__(file, function, tokens, node)

    def what(self) -> str:
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
        file: Path,
        function: "Function",
        tokens: List[Token],
        node: "AaaTreeNode",
        type_stack: TypeStack,
        if_stack: TypeStack,
        else_stack: TypeStack,
    ) -> None:
        self.type_stack = type_stack
        self.if_stack = if_stack
        self.else_stack = else_stack
        super().__init__(file, function, tokens, node)

    def what(self) -> str:
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
        file: Path,
        function: "Function",
        tokens: List[Token],
        node: "AaaTreeNode",
        type_stack: TypeStack,
        loop_stack: TypeStack,
    ) -> None:
        self.type_stack = type_stack
        self.loop_stack = loop_stack
        super().__init__(file, function, tokens, node)

    def what(self) -> str:
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
    def what(self) -> str:
        return (
            f"Function {self.function.name} was already defined.\n"
            + self.get_error_header()
        )


class ArgumentNameCollision(TypeException):
    def what(self) -> str:
        return (
            f"Argument name already used by other argument or function name in {self.function.name}\n"
            + self.get_error_header()
        )


class UnknownFunction(TypeException):
    def what(self) -> str:
        return (
            f"Unknown function or identifier in {self.function.name}\n"
            + self.get_error_header()
        )


class UnknownType(TypeException):
    def what(self) -> str:
        return f"Unknown type in {self.function.name}\n" + self.get_error_header()


class UnknownPlaceholderType(TypeException):
    def what(self) -> str:
        return (
            f"Usage of unknown placeholder type in {self.function.name}\n"
            + self.get_error_header()
        )


class InvalidMainSignuture(TypeException):
    def what(self) -> str:
        return f"Invalid signature for main function\n" + self.get_error_header()

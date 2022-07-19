from pathlib import Path
from typing import List

from lang.exceptions import AaaLoadException, error_location, format_typestack
from lang.models.parse import Function, MemberFunction, Struct
from lang.typing.types import Signature, TypePlaceholder, TypeStack, VariableType


class TypeException(AaaLoadException):
    def __init__(self, file: Path, function: Function) -> None:
        self.file = file
        self.function = function

    def where(self) -> str:
        return error_location(self.file, self.function.token)


class FunctionTypeError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        expected_return_types: List[VariableType | TypePlaceholder],
        computed_return_types: TypeStack,
    ) -> None:
        self.expected_return_types = expected_return_types
        self.computed_return_types = computed_return_types
        super().__init__(file, function)

    def __str__(self) -> str:  # pragma: nocover
        expected = format_typestack(self.expected_return_types)
        found = format_typestack(self.computed_return_types)

        return (
            f"{self.where()}: Function {self.function.name} returns wrong type(s)\n"
            + f"expected return types: {expected}\n"
            + f"   found return types: {found}\n"
        )


class StackUnderflowError(TypeException):
    def __str__(self) -> str:  # pragma: nocover
        return f"{self.where()} Function {self.function.name} has a stack underflow\n"


class StackTypesError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        signature: Signature,
        type_stack: TypeStack,
    ) -> None:
        self.signature = signature
        self.type_stack = type_stack
        super().__init__(file, function)

    def __str__(self) -> str:  # pragma: nocover
        # TODO can we add which function call or operator would get invalid operands?

        return (
            f"{self.where()} Function {self.function.name} has a stack type error\n"
            + "  Type stack: "
            + format_typestack(self.type_stack)
            + "\n"
            "Expected top: " + format_typestack(self.signature.arg_types) + "\n"
        )


class ConditionTypeError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        type_stack: TypeStack,
        condition_stack: TypeStack,
    ) -> None:
        self.type_stack = type_stack
        self.condition_stack = condition_stack
        super().__init__(file, function)

    def __str__(self) -> str:  # pragma: nocover
        return (
            f"{self.where()} Function {self.function.name} has a condition type error\n"
            + "stack before: "
            + format_typestack(self.type_stack)
            + "\n"
            + " stack after: "
            + format_typestack(self.condition_stack)
            + "\n"
        )


class BranchTypeError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        type_stack: TypeStack,
        if_stack: TypeStack,
        else_stack: TypeStack,
    ) -> None:
        self.type_stack = type_stack
        self.if_stack = if_stack
        self.else_stack = else_stack
        super().__init__(file, function)

    def __str__(self) -> str:  # pragma: nocover
        return (
            f"{self.where()} Function {self.function.name} has inconsistent stacks for branches\n"
            + "           before: "
            + format_typestack(self.type_stack)
            + "\n"
            + "  after if-branch: "
            + format_typestack(self.if_stack)
            + "\n"
            + "after else-branch: "
            + format_typestack(self.else_stack)
            + "\n"
        )


class LoopTypeError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        type_stack: TypeStack,
        loop_stack: TypeStack,
    ) -> None:
        self.type_stack = type_stack
        self.loop_stack = loop_stack
        super().__init__(file, function)

    def __str__(self) -> str:  # pragma: nocover
        return (
            f"{self.where()} Function {self.function.name} has a stack modification inside loop body\n"
            + "before loop: "
            + format_typestack(self.type_stack)
            + "\n"
            + " after loop: "
            + format_typestack(self.loop_stack)
            + "\n"
        )


class InvalidMainSignuture(TypeException):
    def __str__(self) -> str:  # pragma: nocover
        # TODO put expected signature
        return f"{self.where()} Main function has invalid signature\n"


class GetFieldOfNonStructTypeError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        type_stack: TypeStack,
    ) -> None:
        self.type_stack = type_stack
        super().__init__(file, function)

    def __str__(self) -> str:  # pragma: nocover
        return (
            f"{self.where()} Function {self.function.name} tries to get field of non-struct value\n"
            + "  Type stack: "
            + format_typestack(self.type_stack)
            + "\n"
            "Expected top: <struct type> str \n"
        )


class SetFieldOfNonStructTypeError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        type_stack: TypeStack,
    ) -> None:
        self.type_stack = type_stack
        super().__init__(file, function)

    def __str__(self) -> str:  # pragma: nocover
        # TODO this just points to start of function
        return (
            f"{self.where()} Function {self.function.name} tries to set field of non-struct value\n"
            + "  Type stack: "
            + format_typestack(self.type_stack)
            + "\n"
            "Expected top: <struct type> str \n"
        )


class StructUpdateStackError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        type_stack: TypeStack,
        type_stack_before: TypeStack,
    ) -> None:
        self.type_stack = type_stack
        self.type_stack_before = type_stack_before
        super().__init__(file, function)

    def __str__(self) -> str:  # pragma: nocover
        # TODO this just points to start of function
        return (
            f"{self.where()} Function {self.function.name} modifies stack incorrectly when updating struct field\n"
            + "  Expected: "
            + format_typestack(self.type_stack_before)
            + f" <new field value> \n"  # TODO put actual expected type for field
            + "    Found: "
            + format_typestack(self.type_stack)
            + "\n"
        )


class StructUpdateTypeError(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        type_stack: TypeStack,
        struct: Struct,
        field_name: str,
        expected_type: VariableType,
        found_type: VariableType,
    ) -> None:
        self.type_stack = type_stack
        self.struct = struct
        self.field_name = field_name
        self.expected_type = expected_type
        self.found_type = found_type
        super().__init__(file, function)

    def __str__(self) -> str:  # pragma: nocover
        # TODO this just points to start of function
        return (
            f"{self.where()} Function {self.function.name} tries to update struct field with wrong type\n"
            f"Attempt to set field {self.field_name} of {self.struct.name} to wrong type in {self.function.name}\n"
            + f"Expected type: {self.expected_type}\n"
            + f"   Found type: {self.found_type}\n"
            + "\n"
            + "Type stack: "
            + format_typestack(self.type_stack)
            + "\n"
        )


class InvalidMemberFunctionSignature(TypeException):
    def __init__(
        self,
        *,
        file: Path,
        function: Function,
        struct: Struct,
        signature: Signature,
    ) -> None:
        self.struct = struct
        self.signature = signature
        self.function = function
        self.file = file

    def __str__(self) -> str:  # pragma: nocover
        assert isinstance(self.function.name, MemberFunction)

        member_func_name = (
            f"{self.function.name.type_name}:{self.function.name.func_name}"
        )

        line = self.function.token.line
        col = self.function.token.column

        formatted = f"{self.file}:{line}:{col} Function {member_func_name} has invalid member-function signature\n\n"

        if (
            len(self.signature.arg_types) == 0
            or str(self.signature.arg_types[0]) != self.struct.name
        ):
            formatted += (
                f"Expected arg types: {self.struct.name} ...\n"
                + f"   Found arg types: {' '.join(str(arg) for arg in self.signature.arg_types)}\n\n"
            )

        if (
            len(self.signature.return_types) == 0
            or str(self.signature.return_types[0]) != self.struct.name
        ):
            formatted += (
                f"Expected return types: {self.struct.name} ...\n"
                + f"   Found return types: {' '.join(str(ret) for ret in self.signature.return_types)}\n\n"
            )

        return formatted

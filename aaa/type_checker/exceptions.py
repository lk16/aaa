from pathlib import Path
from typing import List, Union

from aaa import AaaException, error_location
from aaa.cross_referencer.models import (
    Function,
    MemberFunctionName,
    Operator,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
    VariableType,
)
from aaa.type_checker.models import (
    Signature,
    StructQuerySignature,
    StructUpdateSignature,
)


def format_typestack(
    type_stack: List[VariableType],
) -> str:
    return " ".join(repr(type_stack_item) for type_stack_item in type_stack)


class TypeCheckerException(AaaException):
    def __init__(self, file: Path, function: Function) -> None:
        self.file = file
        self.function = function


class TypeException(TypeCheckerException):
    def __init__(self, *, file: Path, function: Function) -> None:
        self.file = file
        self.function = function

    def where(self) -> str:
        return error_location(self.file, self.function.parsed.token)


class FunctionTypeError(TypeCheckerException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        expected_return_types: List[VariableType],
        computed_return_types: List[VariableType],
    ) -> None:
        self.expected_return_types = expected_return_types
        self.computed_return_types = computed_return_types
        super().__init__(file=file, function=function)

    def where(self) -> str:
        # TODO
        raise NotImplementedError

    def __str__(self) -> str:
        expected = format_typestack(self.expected_return_types)
        found = format_typestack(self.computed_return_types)

        return (
            f"{self.where()}: Function {self.function.name} returns wrong type(s)\n"
            + f"expected return types: {expected}\n"
            + f"   found return types: {found}\n"
        )


class StackTypesError(TypeCheckerException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        signature: Union[Signature, StructQuerySignature, StructUpdateSignature],
        type_stack: List[VariableType],
        func_like: Union[
            Operator,
            Function,
            MemberFunctionName,
            StructFieldUpdate,
            StructFieldQuery,
        ],
    ) -> None:
        self.signature = signature
        self.type_stack = type_stack
        self.func_like = func_like
        super().__init__(file=file, function=function)

    def func_like_name(self) -> str:
        if isinstance(self.func_like, Operator):
            return self.func_like.value
        elif isinstance(self.func_like, Function):
            assert isinstance(self.func_like.name, str)
            return self.func_like.name
        elif isinstance(self.func_like, MemberFunctionName):
            return f"{self.func_like.struct_name.identifier.name}:{self.func_like.func_name.name}"
        else:
            assert False

    def format_typestack(self) -> str:
        if isinstance(self.signature, Signature):
            return format_typestack(self.signature.arguments)
        elif isinstance(self.signature, StructQuerySignature):
            return "<struct type> str"
        elif isinstance(self.signature, StructUpdateSignature):
            return "<struct type> str <type of field to update>"
        else:  # pragma:nocover
            assert False

    def where(self) -> str:
        # TODO
        raise NotImplementedError

    def __str__(self) -> str:
        return (
            f"{self.where()} Function {self.function.name} has invalid stack types when calling {self.func_like_name()}\n"
            + f"Expected stack top: {self.format_typestack()}\n"
            + f"       Found stack: {format_typestack(self.type_stack)}\n"
        )


class ConditionTypeError(TypeCheckerException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        type_stack: List[VariableType],
        condition_stack: List[VariableType],
    ) -> None:
        self.type_stack = type_stack
        self.condition_stack = condition_stack
        super().__init__(file=file, function=function)

    def where(self) -> str:
        # TODO
        raise NotImplementedError

    def __str__(self) -> str:
        stack_before = format_typestack(self.type_stack)
        stack_after = format_typestack(self.condition_stack)

        return (
            f"{self.where()} Function {self.function.name} has a condition type error\n"
            + f"stack before: {stack_before}\n"
            + f" stack after: {stack_after}\n"
        )


class BranchTypeError(TypeCheckerException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        type_stack: List[VariableType],
        if_stack: List[VariableType],
        else_stack: List[VariableType],
    ) -> None:
        self.type_stack = type_stack
        self.if_stack = if_stack
        self.else_stack = else_stack
        super().__init__(file=file, function=function)

    def where(self) -> str:
        # TODO
        raise NotImplementedError

    def __str__(self) -> str:
        before_stack = format_typestack(self.type_stack)
        if_stack = format_typestack(self.if_stack)
        else_stack = format_typestack(self.else_stack)

        return (
            f"{self.where()} Function {self.function.name} has inconsistent stacks for branches\n"
            + f"           before: {before_stack}\n"
            + f"  after if-branch: {if_stack}\n"
            + f"after else-branch: {else_stack}\n"
        )


class LoopTypeError(TypeCheckerException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        type_stack: List[VariableType],
        loop_stack: List[VariableType],
    ) -> None:
        self.type_stack = type_stack
        self.loop_stack = loop_stack
        super().__init__(file=file, function=function)

    def where(self) -> str:
        # TODO
        raise NotImplementedError

    def __str__(self) -> str:
        before_stack = format_typestack(self.type_stack)
        after_stack = format_typestack(self.loop_stack)

        return (
            f"{self.where()} Function {self.function.name} has a stack modification inside loop body\n"
            + f"before loop: {before_stack}\n"
            + f" after loop: {after_stack}\n"
        )


class InvalidMainSignuture(TypeCheckerException):
    def where(self) -> str:
        return error_location(self.file, self.function.parsed.token)

    def __str__(self) -> str:
        return f"{self.where()} Main function should have no arguments and no return types\n"


class GetFieldOfNonStructTypeError(TypeCheckerException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        type_stack: List[VariableType],
        field_query: StructFieldQuery,
    ) -> None:
        self.type_stack = type_stack
        self.field_query = field_query
        super().__init__(file=file, function=function)

    def where(self) -> str:
        return error_location(self.file, self.field_query.token)

    def __str__(self) -> str:
        stack = format_typestack(self.type_stack)

        return (
            f"{self.where()} Function {self.function.name} tries to get field of non-struct value\n"
            + f"  Type stack: {stack}\n"
            + "Expected top: <struct type> str \n"
        )


class SetFieldOfNonStructTypeError(TypeCheckerException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        type_stack: List[VariableType],
        field_update: StructFieldUpdate,
    ) -> None:
        self.type_stack = type_stack
        self.field_update = field_update
        super().__init__(file=file, function=function)

    def where(self) -> str:
        return error_location(self.file, self.field_update.token)

    def __str__(self) -> str:
        stack = format_typestack(self.type_stack)

        return (
            f"{self.where()} Function {self.function.name} tries to set field of non-struct value\n"
            + f"  Type stack: {stack}\n"
            + "Expected top: <struct type> str <type of field to update>\n"
        )


class StructUpdateStackError(TypeCheckerException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        type_stack: List[VariableType],
        type_stack_before: List[VariableType],
        field_update: StructFieldUpdate,
    ) -> None:
        self.type_stack = type_stack
        self.type_stack_before = type_stack_before
        self.field_update = field_update
        super().__init__(file=file, function=function)

    def where(self) -> str:
        return error_location(self.file, self.field_update.token)

    def __str__(self) -> str:
        expected_stack = format_typestack(self.type_stack_before)
        found_stack = format_typestack(self.type_stack)

        return (
            f"{self.where()} Function {self.function.name} modifies stack incorrectly when updating struct field\n"
            + f"  Expected: {expected_stack} <new field value> \n"
            + f"    Found: {found_stack}\n"
        )


class StructUpdateTypeError(TypeCheckerException):
    def __init__(
        self,
        *,
        file: Path,
        function: "Function",
        type_stack: List[VariableType],
        struct_type: Type,
        field_name: str,
        expected_type: VariableType,
        found_type: VariableType,
        field_update: StructFieldUpdate,
    ) -> None:
        self.type_stack = type_stack
        self.struct_type = struct_type
        self.field_name = field_name
        self.expected_type = expected_type
        self.found_type = found_type
        self.field_update = field_update
        super().__init__(file=file, function=function)

    def where(self) -> str:
        return error_location(self.file, self.field_update.token)

    def __str__(self) -> str:
        return (
            f"{self.where()} Function {self.function.name} tries to update struct field with wrong type\n"
            f"Attempt to set field {self.field_name} of {self.struct_type.name} to wrong type in {self.function.name}\n"
            + f"Expected type: {self.expected_type}\n"
            + f"   Found type: {self.found_type}\n"
            + "\n"
            + "Type stack: "
            + format_typestack(self.type_stack)
            + "\n"
        )


class InvalidMemberFunctionSignature(TypeCheckerException):
    def __init__(
        self,
        *,
        file: Path,
        function: Function,
        struct_type: Type,
        signature: Signature,
    ) -> None:
        self.struct_type = struct_type
        self.signature = signature
        self.function = function
        self.file = file

    def __str__(self) -> str:
        member_func_name = f"{self.function.struct_name}:{self.function.name}"

        line = self.function.parsed.token.line
        col = self.function.parsed.token.column

        formatted = f"{self.file}:{line}:{col} Function {member_func_name} has invalid member-function signature\n\n"

        if (
            len(self.signature.arguments) == 0
            or str(self.signature.arguments[0]) != self.struct_type.name
        ):
            formatted += (
                f"Expected arg types: {self.struct_type.name} ...\n"
                + f"   Found arg types: {' '.join(str(arg) for arg in self.signature.arguments)}\n"
            )

        if (
            len(self.signature.return_types) == 0
            or str(self.signature.return_types[0]) != self.struct_type.name
        ):
            formatted += (
                f"Expected return types: {self.struct_type.name} ...\n"
                + f"   Found return types: {' '.join(str(ret) for ret in self.signature.return_types)}\n"
            )

        return formatted


class UnknownStructField(TypeCheckerException):
    def __init__(
        self, file: Path, function: Function, struct_type: Type, field_name: str
    ) -> None:
        self.file = file
        self.function = function
        self.struct_type = struct_type
        self.field_name = field_name

    def __str__(self) -> str:
        # TODO
        raise NotImplementedError

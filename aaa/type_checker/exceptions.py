from pathlib import Path
from typing import List, Union

from aaa import AaaException, Position
from aaa.cross_referencer.models import (
    Function,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
    VariableType,
)


def format_typestack(
    type_stack: List[VariableType],
) -> str:
    return " ".join(repr(type_stack_item) for type_stack_item in type_stack)


class TypeCheckerException(AaaException):
    def __init__(self, position: Position, function: Function) -> None:
        self.position = position
        self.function = function


class TypeException(TypeCheckerException):
    ...


class FunctionTypeError(TypeCheckerException):
    def __init__(
        self, function: Function, computed_return_types: List[VariableType]
    ) -> None:
        self.computed_return_types = computed_return_types
        super().__init__(function.position, function)

    def __str__(self) -> str:
        expected = format_typestack(self.function.return_types)
        found = format_typestack(self.computed_return_types)

        return (
            f"{self.function.position}: Function {self.function.name} returns wrong type(s)\n"
            + f"expected return types: {expected}\n"
            + f"   found return types: {found}\n"
        )


class StackTypesError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        function: Function,
        type_stack: List[VariableType],
        func_like: Union[Function, StructFieldUpdate, StructFieldQuery],
    ) -> None:
        self.type_stack = type_stack
        self.func_like = func_like
        super().__init__(position, function)

    def func_like_name(self) -> str:
        if isinstance(self.func_like, Function):
            return self.func_like.name
        elif isinstance(self.func_like, StructFieldQuery):
            return "?"
        elif isinstance(self.func_like, StructFieldUpdate):
            return "!"
        else:
            assert False

    def format_typestack(self) -> str:
        if isinstance(self.func_like, Function):
            types = [arg.var_type for arg in self.func_like.arguments]
            return format_typestack(types)
        elif isinstance(self.func_like, StructFieldQuery):
            return "<struct type> str"
        elif isinstance(self.func_like, StructFieldUpdate):
            return "<struct type> str <type of field to update>"
        else:  # pragma:nocover
            assert False

    def __str__(self) -> str:
        return (
            f"{self.position} Function {self.function.name} has invalid stack types when calling {self.func_like_name()}\n"
            + f"Expected stack top: {self.format_typestack()}\n"
            + f"       Found stack: {format_typestack(self.type_stack)}\n"
        )


class ConditionTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        function: Function,
        type_stack: List[VariableType],
        condition_stack: List[VariableType],
    ) -> None:
        self.type_stack = type_stack
        self.condition_stack = condition_stack
        super().__init__(position, function)

    def __str__(self) -> str:
        stack_before = format_typestack(self.type_stack)
        stack_after = format_typestack(self.condition_stack)

        return (
            f"{self.position} Function {self.function.name} has a condition type error\n"
            + f"stack before: {stack_before}\n"
            + f" stack after: {stack_after}\n"
        )


class BranchTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        function: Function,
        type_stack: List[VariableType],
        if_stack: List[VariableType],
        else_stack: List[VariableType],
    ) -> None:
        self.type_stack = type_stack
        self.if_stack = if_stack
        self.else_stack = else_stack
        super().__init__(position, function)

    def __str__(self) -> str:
        before_stack = format_typestack(self.type_stack)
        if_stack = format_typestack(self.if_stack)
        else_stack = format_typestack(self.else_stack)

        return (
            f"{self.position} Function {self.function.name} has inconsistent stacks for branches\n"
            + f"           before: {before_stack}\n"
            + f"  after if-branch: {if_stack}\n"
            + f"after else-branch: {else_stack}\n"
        )


class WhileLoopTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        function: Function,
        type_stack: List[VariableType],
        loop_stack: List[VariableType],
    ) -> None:
        self.type_stack = type_stack
        self.loop_stack = loop_stack
        super().__init__(position, function)

    def __str__(self) -> str:
        before_stack = format_typestack(self.type_stack)
        after_stack = format_typestack(self.loop_stack)

        return (
            f"{self.position} Function {self.function.name} has a stack modification inside while loop body\n"
            + f"before while loop: {before_stack}\n"
            + f" after while loop: {after_stack}\n"
        )


class InvalidMainSignuture(TypeCheckerException):
    def __str__(self) -> str:
        return f"{self.position} Main function should have no type parameters, no arguments and no return types\n"


class InvalidTestSignuture(TypeCheckerException):
    def __init__(self, function: Function) -> None:
        super().__init__(function.position, function)

    def __str__(self) -> str:
        return f"{self.position} Test function {self.function.name} should have no arguments and no return types\n"


class StructUpdateStackError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        function: Function,
        type_stack: List[VariableType],
        type_stack_before: List[VariableType],
    ) -> None:
        self.type_stack = type_stack
        self.type_stack_before = type_stack_before
        super().__init__(position, function)

    def __str__(self) -> str:
        expected_stack = format_typestack(self.type_stack_before)
        found_stack = format_typestack(self.type_stack)

        return (
            f"{self.position} Function {self.function.name} modifies stack incorrectly when updating struct field\n"
            + f"  Expected: {expected_stack} <new field value> \n"
            + f"    Found: {found_stack}\n"
        )


class StructUpdateTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        function: Function,
        type_stack: List[VariableType],
        struct_type: Type,
        field_name: str,
        expected_type: VariableType,
        found_type: VariableType,
    ) -> None:
        self.type_stack = type_stack
        self.struct_type = struct_type
        self.field_name = field_name
        self.expected_type = expected_type
        self.found_type = found_type
        super().__init__(position, function)

    def __str__(self) -> str:
        return (
            f"{self.position} Function {self.function.name} tries to update struct field with wrong type\n"
            + f"Attempt to set field {self.field_name} of {self.struct_type.name} to wrong type in {self.function.name}\n"
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
        function: Function,
        struct_type: Type,
    ) -> None:
        self.struct_type = struct_type
        super().__init__(function.position, function)

    def __str__(self) -> str:
        full_func_name = f"{self.function.struct_name}:{self.function.func_name}"
        formatted = f"{self.position} Function {full_func_name} has invalid member-function signature\n\n"

        arguments = [arg.var_type for arg in self.function.arguments]

        if len(arguments) == 0 or arguments[0].type != self.struct_type:
            formatted += (
                f"Expected arg types: {self.struct_type.name} ...\n"
                + f"   Found arg types: {' '.join(str(arg.type) for arg in arguments)}\n"
            )

        return formatted


class UnknownField(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        function: Function,
        struct_type: Type,
        field_name: str,
    ) -> None:
        self.struct_type = struct_type
        self.field_name = field_name
        super().__init__(position, function)

    def __str__(self) -> str:
        return f"{self.position}: Usage of unknown field {self.field_name} of type {self.struct_type.name}"


class MainFunctionNotFound(TypeCheckerException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f"{self.file}: No main function found"

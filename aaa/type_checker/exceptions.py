from pathlib import Path
from typing import List, Union

from aaa import AaaException, Position
from aaa.cross_referencer.models import (
    Assignment,
    Function,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
    UseBlock,
    Variable,
    VariableType,
)


def format_typestack(type_stack: List[VariableType]) -> str:
    return " ".join(repr(item) for item in type_stack)


class TypeCheckerException(AaaException):
    def __init__(self, position: Position) -> None:
        self.position = position


class FunctionTypeError(TypeCheckerException):
    def __init__(
        self, function: Function, computed_return_types: List[VariableType]
    ) -> None:
        self.computed_return_types = computed_return_types
        self.function = function
        super().__init__(function.position)

    def __str__(self) -> str:
        expected = format_typestack(self.function.return_types)
        found = format_typestack(self.computed_return_types)

        return (
            f"{self.position}: Function {self.function.name} returns wrong type(s)\n"
            + f"expected return types: {expected}\n"
            + f"   found return types: {found}\n"
        )


class StackTypesError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: List[VariableType],
        func_like: Union[Function, StructFieldUpdate, StructFieldQuery],
    ) -> None:
        self.type_stack = type_stack
        self.func_like = func_like
        super().__init__(position)

    def func_like_name(self) -> str:  # pragma: nocover
        if isinstance(self.func_like, Function):
            return self.func_like.name
        elif isinstance(self.func_like, StructFieldQuery):
            return "?"
        elif isinstance(self.func_like, StructFieldUpdate):
            return "!"
        else:
            assert False

    def format_typestack(self) -> str:  # pragma: nocover
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
            f"{self.position}: Invalid stack types when calling {self.func_like_name()}\n"
            + f"Expected stack top: {self.format_typestack()}\n"
            + f"       Found stack: {format_typestack(self.type_stack)}\n"
        )


class ConditionTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: List[VariableType],
        condition_stack: List[VariableType],
    ) -> None:
        self.type_stack = type_stack
        self.condition_stack = condition_stack
        super().__init__(position)

    def __str__(self) -> str:
        stack_before = format_typestack(self.type_stack)
        stack_after = format_typestack(self.condition_stack)

        return (
            f"{self.position}: Condition type error\n"
            + f"stack before: {stack_before}\n"
            + f" stack after: {stack_after}\n"
        )


class BranchTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: List[VariableType],
        if_stack: List[VariableType],
        else_stack: List[VariableType],
    ) -> None:
        self.type_stack = type_stack
        self.if_stack = if_stack
        self.else_stack = else_stack
        super().__init__(position)

    def __str__(self) -> str:
        before_stack = format_typestack(self.type_stack)
        if_stack = format_typestack(self.if_stack)
        else_stack = format_typestack(self.else_stack)

        return (
            f"{self.position}: Inconsistent stacks for branches\n"
            + f"           before: {before_stack}\n"
            + f"  after if-branch: {if_stack}\n"
            + f"after else-branch: {else_stack}\n"
        )


class WhileLoopTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: List[VariableType],
        loop_stack: List[VariableType],
    ) -> None:
        self.type_stack = type_stack
        self.loop_stack = loop_stack
        super().__init__(position)

    def __str__(self) -> str:
        before_stack = format_typestack(self.type_stack)
        after_stack = format_typestack(self.loop_stack)

        return (
            f"{self.position}: Invalid stack modification inside while loop body\n"
            + f"before while loop: {before_stack}\n"
            + f" after while loop: {after_stack}\n"
        )


class InvalidMainSignuture(TypeCheckerException):
    def __str__(self) -> str:
        return (
            f"{self.position}: Main function has wrong signature, it should have:\n"
            + "- no type parameters\n"
            + "- either no arguments or one vec[str] argument\n"
            + "- return either nothing or an int\n"
        )


class InvalidTestSignuture(TypeCheckerException):
    def __init__(self, function: Function) -> None:
        self.function = function
        super().__init__(function.position)

    def __str__(self) -> str:
        return f"{self.position}: Test function {self.function.name} should have no arguments and no return types\n"


class StructUpdateStackError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: List[VariableType],
        type_stack_before: List[VariableType],
    ) -> None:
        self.type_stack = type_stack
        self.type_stack_before = type_stack_before
        super().__init__(position)

    def __str__(self) -> str:
        expected_stack = format_typestack(self.type_stack_before)
        found_stack = format_typestack(self.type_stack)

        return (
            f"{self.position}: Incorrect stack modification when updating struct field\n"
            + f"  Expected: {expected_stack} <new field value> \n"
            + f"     Found: {found_stack}\n"
        )


class StructUpdateTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
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
        super().__init__(position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Attempt to set field {self.field_name} of {self.struct_type.name} to wrong type\n"
            + f"Expected type: {self.expected_type}\n"
            + f"   Found type: {self.found_type}\n"
            + "\n"
            + "Type stack: "
            + format_typestack(self.type_stack)
            + "\n"
        )


class InvalidMemberFunctionSignature(TypeCheckerException):
    def __init__(self, function: Function, struct_type: Type) -> None:
        self.struct_type = struct_type
        self.function = function
        super().__init__(function.position)

    def __str__(self) -> str:
        full_func_name = f"{self.function.struct_name}:{self.function.func_name}"
        formatted = f"{self.position}: Function {full_func_name} has invalid member-function signature\n\n"

        arguments = [arg.var_type for arg in self.function.arguments]

        if len(arguments) == 0 or arguments[0].type != self.struct_type:
            formatted += (
                f"Expected arg types: {self.struct_type.name} ...\n"
                + f"   Found arg types: {' '.join(str(arg.type) for arg in arguments)}\n"
            )

        return formatted


class UnknownField(TypeCheckerException):
    def __init__(self, position: Position, struct_type: Type, field_name: str) -> None:
        self.struct_type = struct_type
        self.field_name = field_name
        super().__init__(position)

    def __str__(self) -> str:
        return f"{self.position}: Usage of unknown field {self.field_name} of type {self.struct_type.name}\n"


class MainFunctionNotFound(TypeCheckerException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f"{self.file}: No main function found\n"


class MissingIterable(TypeCheckerException):
    def __str__(self) -> str:
        return f"{self.position}: Cannot use foreach, function stack is empty.\n"


class InvalidIterable(TypeCheckerException):
    def __init__(self, position: Position, iterable_type: VariableType) -> None:
        self.iterable_type = iterable_type
        super().__init__(position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Invalid iterable type {self.iterable_type}.\n"
            + "Iterable types need to have a function named iter which:\n"
            + "- takes one argument (the iterable)\n"
            + "- returns one value (an iterator)\n"
        )


class InvalidIterator(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        iterable_type: VariableType,
        iterator_type: VariableType,
    ) -> None:
        self.iterable_type = iterable_type
        self.iterator_type = iterator_type
        super().__init__(position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Invalid iterator type {self.iterator_type} to iterate over {self.iterable_type}.\n"
            + "Iterator types need to have a function named next which:\n"
            + "- takes one argument (the iterator)\n"
            + "- returns at least 2 values, the last being a boolean\n"
            + "- indicates if more data is present in the iterable with this last return value\n"
            + "- for const iterators all return values of `next` except the last one must be const\n"
        )


class ForeachLoopTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: List[VariableType],
        foreach_stack: List[VariableType],
    ) -> None:
        self.type_stack = type_stack
        self.foreach_stack = foreach_stack
        super().__init__(position)

    def __str__(self) -> str:
        before_stack = format_typestack(self.type_stack)
        after_stack = format_typestack(self.foreach_stack)

        return (
            f"{self.position}: Invalid stack modification inside foreach loop body\n"
            + f"before foreach loop: {before_stack}\n"
            + f" after foreach loop: {after_stack}\n"
        )


class UseBlockStackUnderflow(TypeCheckerException):
    def __init__(self, stack_size: int, use_block: UseBlock) -> None:
        self.stack_size = stack_size
        self.use_block_vars = len(use_block.variables)
        super().__init__(use_block.position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Use block consumes more values than can be found on the stack\n"
            + f"    stack size: {self.stack_size}\n"
            + f"used variables: {self.use_block_vars}\n"
        )


class AssignmentTypeError(TypeCheckerException):
    def __init__(
        self,
        expected_var_types: List[VariableType],
        found_var_types: List[VariableType],
        assignment: Assignment,
    ) -> None:
        self.expected_var_types = expected_var_types
        self.found_var_types = found_var_types
        super().__init__(assignment.position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Assignment with wrong number and/or type of values\n"
            + f"expected types: "
            + " ".join(str(var_type) for var_type in self.expected_var_types)
            + "\n"
            + f"   found types: "
            + " ".join(str(var_type) for var_type in self.found_var_types)
            + "\n"
        )


class UpdateConstStructError(TypeCheckerException):
    def __init__(self, field_update: StructFieldUpdate, struct_name: str) -> None:
        self.field_name = field_update.field_name.value
        self.struct_name = struct_name
        super().__init__(field_update.position)

    def __str__(self) -> str:
        return f"{self.position}: Cannot update field {self.field_name} on const struct {self.struct_name}\n"


class AssignConstValueError(TypeCheckerException):
    def __init__(self, var: Variable, type: VariableType) -> None:
        self.var_name = var.name
        self.type = type
        super().__init__(var.position)

    def __str__(self) -> str:
        return f"{self.position}: Cannot assign to {self.type} {self.var_name}\n"


class MemberFunctionTypeNotFound(TypeCheckerException):
    def __init__(self, function: Function) -> None:
        self.function = function

    def __str__(self) -> str:
        struct_name = self.function.struct_name
        return f"{self.function.position}: Cannot find type {struct_name} in same file as member function definition.\n"


class SignatureItemMismatch(AaaException):
    ...

from pathlib import Path

from basil.models import Position

from aaa import AaaException
from aaa.cross_referencer.exceptions import describe
from aaa.cross_referencer.models import (
    Argument,
    Assignment,
    CallFunctionByPointer,
    CallVariable,
    CaseBlock,
    DefaultBlock,
    Enum,
    EnumConstructor,
    Function,
    FunctionPointer,
    MatchBlock,
    Never,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    UseBlock,
    Variable,
    VariableType,
)


def format_typestack(
    type_stack: list[VariableType | FunctionPointer] | Never,
) -> str:
    if isinstance(type_stack, Never):
        return "never"

    return " ".join(repr(item) for item in type_stack)


class TypeCheckerException(AaaException):
    def __init__(self, position: Position) -> None:
        self.position = position


class FunctionTypeError(TypeCheckerException):
    def __init__(
        self,
        function: Function,
        computed_return_types: list[VariableType | FunctionPointer] | Never,
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
            + f"   found return types: {found}"
        )


class StackTypesError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: list[VariableType | FunctionPointer],
        func_like: Function
        | EnumConstructor
        | CallFunctionByPointer
        | StructFieldUpdate
        | StructFieldQuery,
        type_params: list[VariableType | FunctionPointer] | None = None,
        expected_stack_top_override: list[VariableType | FunctionPointer] | None = None,
    ) -> None:
        self.type_stack = type_stack
        self.func_like = func_like
        self.type_params = type_params or []
        self.expected_stack_top_override = expected_stack_top_override
        super().__init__(position)

    def func_like_name(self) -> str:  # pragma: nocover
        if isinstance(self.func_like, Function | EnumConstructor):
            name = self.func_like.name

            if self.type_params:
                name += "[" + ",".join(repr(param) for param in self.type_params) + "]"

            return name

        elif isinstance(self.func_like, StructFieldQuery):
            return "?"
        elif isinstance(self.func_like, StructFieldUpdate):
            return "!"
        else:
            assert isinstance(self.func_like, CallFunctionByPointer)
            try:
                return repr(self.type_stack[-1])
            except IndexError:
                return "<function pointer>"

    def format_expected_typestack(self) -> str:  # pragma: nocover
        if self.expected_stack_top_override is not None:
            return format_typestack(self.expected_stack_top_override)

        if isinstance(self.func_like, Function):
            types = [arg.type for arg in self.func_like.arguments]
            return format_typestack(types)
        elif isinstance(self.func_like, StructFieldQuery):
            return "<struct type> str"
        elif isinstance(self.func_like, StructFieldUpdate):
            return "<struct type> str <type of field to update>"
        elif isinstance(self.func_like, CallFunctionByPointer):
            try:
                func_ptr = self.type_stack[-1]
            except IndexError:
                return "<argument types>... <function pointer>"

            if isinstance(func_ptr, FunctionPointer):
                return " ".join(
                    repr(item) for item in func_ptr.argument_types + [func_ptr]
                )
            return "<argument types>... <function pointer>"

        else:
            assert isinstance(self.func_like, EnumConstructor)
            types = self.func_like.enum.variants[self.func_like.variant_name]
            return format_typestack(types)

    def __str__(self) -> str:
        return (
            f"{self.position}: Invalid stack types when calling "
            + f"{self.func_like_name()}\n"
            + "Expected stack top: "
            + self.format_expected_typestack()
            + "\n"
            + "       Found stack: "
            + format_typestack(self.type_stack)
        )


class ConditionTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: list[VariableType | FunctionPointer],
        condition_stack: list[VariableType | FunctionPointer],
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
            + f" stack after: {stack_after}"
        )


class BranchTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: list[VariableType | FunctionPointer],
        if_stack: list[VariableType | FunctionPointer],
        else_stack: list[VariableType | FunctionPointer],
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
            + f"after else-branch: {else_stack}"
        )


class WhileLoopTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: list[VariableType | FunctionPointer],
        loop_stack: list[VariableType | FunctionPointer],
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
            + f" after while loop: {after_stack}"
        )


class InvalidMainSignuture(TypeCheckerException):
    def __str__(self) -> str:
        return (
            f"{self.position}: Main function has wrong signature, it should have:\n"
            + "- no type parameters\n"
            + "- either no arguments or one vec[str] argument\n"
            + "- return either nothing or an int"
        )


class InvalidTestSignuture(TypeCheckerException):
    def __init__(self, function: Function) -> None:
        self.function = function
        super().__init__(function.position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Test function {self.function.name} should have no "
            + "arguments and no return types"
        )


class StructUpdateStackError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: list[VariableType | FunctionPointer],
        type_stack_before: list[VariableType | FunctionPointer],
    ) -> None:
        self.type_stack = type_stack
        self.type_stack_before = type_stack_before
        super().__init__(position)

    def __str__(self) -> str:
        expected_stack = format_typestack(self.type_stack_before)
        found_stack = format_typestack(self.type_stack)

        return (
            f"{self.position}: Incorrect stack modification when updating "
            + "struct field\n"
            + f"  Expected: {expected_stack} <new field value> \n"
            + f"     Found: {found_stack}"
        )


class StructUpdateTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: list[VariableType | FunctionPointer],
        struct_type: Struct,
        field_name: str,
        expected_type: VariableType | FunctionPointer,
        found_type: VariableType | FunctionPointer,
    ) -> None:
        self.type_stack = type_stack
        self.struct_type = struct_type
        self.field_name = field_name
        self.expected_type = expected_type
        self.found_type = found_type
        super().__init__(position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Attempt to set field {self.field_name} of "
            + f"{self.struct_type.name} to wrong type\n"
            + f"Expected type: {self.expected_type}\n"
            + f"   Found type: {self.found_type}\n"
            + "\n"
            + "Type stack: "
            + format_typestack(self.type_stack)
        )


class InvalidMemberFunctionSignature(TypeCheckerException):
    def __init__(self, function: Function, type: Struct | Enum) -> None:
        self.type = type
        self.function = function
        super().__init__(function.position)

    def __str__(self) -> str:
        full_func_name = f"{self.function.struct_name}:{self.function.func_name}"
        formatted = (
            f"{self.position}: Function {full_func_name} has invalid "
            + "member-function signature\n\n"
        )

        arguments = [arg.type for arg in self.function.arguments]

        formatted += (
            f"Expected arg types: {self.type.name} ...\n"
            + f"   Found arg types: {' '.join(repr(arg) for arg in arguments)}"
        )

        return formatted


class UnknownField(TypeCheckerException):
    def __init__(
        self, position: Position, struct_type: Struct, field_name: str
    ) -> None:
        self.struct_type = struct_type
        self.field_name = field_name
        super().__init__(position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Usage of unknown field {self.field_name} of type "
            + self.struct_type.name
        )


class MainFunctionNotFound(TypeCheckerException):
    def __init__(self, file: Path) -> None:
        self.file = file

    def __str__(self) -> str:
        return f"{self.file}: No main function found"


class MissingIterable(TypeCheckerException):
    def __str__(self) -> str:
        return f"{self.position}: Cannot use foreach, function stack is empty."


class InvalidIterable(TypeCheckerException):
    def __init__(
        self, position: Position, iterable_type: VariableType | FunctionPointer
    ) -> None:
        self.iterable_type = iterable_type
        super().__init__(position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Invalid iterable type {self.iterable_type}.\n"
            + "Iterable types need to have a function named iter which:\n"
            + "- takes one argument (the iterable)\n"
            + "- returns one value (an iterator)"
        )


class InvalidIterator(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        iterable_type: VariableType,
        iterator_type: VariableType | FunctionPointer,
    ) -> None:
        self.iterable_type = iterable_type
        self.iterator_type = iterator_type
        super().__init__(position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Invalid iterator type {self.iterator_type} "
            + f"to iterate over {self.iterable_type}.\n"
            + "Iterator types need to have a function named next which:\n"
            + "- takes one argument (the iterator)\n"
            + "- returns at least 2 values, the last being a boolean\n"
            + "- indicates if more data is present in the iterable with "
            + "this last return value\n"
            + "- for const iterators all return values of `next` except "
            + "the last one must be const"
        )


class ForeachLoopTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        expected_type_stack_after: list[VariableType | FunctionPointer],
        type_stack_after: list[VariableType | FunctionPointer],
    ) -> None:
        self.type_stack_after = type_stack_after
        self.expected_type_stack_after = expected_type_stack_after
        super().__init__(position)

    def __str__(self) -> str:
        stack_after = format_typestack(self.type_stack_after)
        expected_stack_after = format_typestack(self.expected_type_stack_after)

        return (
            f"{self.position}: Invalid stack modification inside foreach loop body\n"
            + f"stack at end of foreach loop: {stack_after}\n"
            + f"              expected stack: {expected_stack_after}"
        )


class UseBlockStackUnderflow(TypeCheckerException):
    def __init__(self, stack_size: int, use_block: UseBlock) -> None:
        self.stack_size = stack_size
        self.use_block_vars = len(use_block.variables)
        super().__init__(use_block.position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Use block consumes more values "
            + "than can be found on the stack\n"
            + f"    stack size: {self.stack_size}\n"
            + f"used variables: {self.use_block_vars}"
        )


class AssignmentTypeError(TypeCheckerException):
    def __init__(
        self,
        expected_var_types: list[VariableType | FunctionPointer],
        found_var_types: list[VariableType | FunctionPointer],
        assignment: Assignment,
    ) -> None:
        self.expected_var_types = expected_var_types
        self.found_var_types = found_var_types
        super().__init__(assignment.position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Assignment with wrong number and/or type of values\n"
            + "expected types: "
            + " ".join(str(var_type) for var_type in self.expected_var_types)
            + "\n"
            + "   found types: "
            + " ".join(str(var_type) for var_type in self.found_var_types)
        )


class UpdateConstStructError(TypeCheckerException):
    def __init__(self, field_update: StructFieldUpdate, struct_name: str) -> None:
        self.field_name = field_update.field_name.value
        self.struct_name = struct_name
        super().__init__(field_update.position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Cannot update field {self.field_name} on "
            + f"const struct {self.struct_name}"
        )


class AssignConstValueError(TypeCheckerException):
    def __init__(self, var: Variable, type: VariableType) -> None:
        self.var_name = var.name
        self.type = type
        super().__init__(var.position)

    def __str__(self) -> str:
        return f"{self.position}: Cannot assign to {self.type} {self.var_name}"


class MemberFunctionTypeNotFound(TypeCheckerException):
    def __init__(self, function: Function) -> None:
        self.function = function

    def __str__(self) -> str:
        struct_name = self.function.struct_name
        return (
            f"{self.function.position}: Cannot find type {struct_name} in "
            + "same file as member function definition."
        )


class InvalidEqualsFunctionSignature(TypeCheckerException):
    def __init__(self, function: Function) -> None:
        self.function = function

    def __str__(self) -> str:
        return (
            f"{self.function.position}: Invalid equals function signature.\n"
            + "An equals function should have:\n"
            + "- 2 const arguments of same type\n"
            + "- 1 return value, which is a boolean"
        )


class UnreachableCode(TypeCheckerException):
    def __str__(self) -> str:
        return f"{self.position}: Found unreachable code."


class ReturnTypesError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: list[VariableType | FunctionPointer],
        function: Function,
    ) -> None:
        self.type_stack = type_stack
        self.function = function
        super().__init__(position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Invalid stack types when returning.\n"
            + f"function returns: {format_typestack(self.function.return_types)}\n"
            + f"     found stack: {format_typestack(self.type_stack)}"
        )


class MatchTypeError(TypeCheckerException):
    def __init__(
        self,
        match_block: MatchBlock,
        type_stack: list[VariableType | FunctionPointer],
    ) -> None:
        self.match_block = match_block
        self.type_stack = type_stack
        super().__init__(match_block.position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Cannot match on this stack:\n"
            + "expected stack types: <enum type>\n"
            + f"   found stack types: {format_typestack(self.type_stack)}"
        )


class CaseEnumTypeError(TypeCheckerException):
    def __init__(
        self, case_block: CaseBlock, expected_enum: Enum, found_enum: Enum
    ) -> None:
        self.match_block = case_block
        self.expected_enum = expected_enum
        self.found_enum = found_enum
        super().__init__(case_block.position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Cannot use case for enum {self.found_enum.name} "
            + f"when matching on enum {self.expected_enum.name}"
        )


def describe_block(block: CaseBlock | DefaultBlock) -> str:
    if isinstance(block, CaseBlock):
        return f"case {block.enum_type.name}:{block.variant_name}"
    else:
        return "default"


class CaseStackTypeError(TypeCheckerException):
    def __init__(
        self,
        blocks: list[CaseBlock | DefaultBlock],
        block_type_stacks: list[list[VariableType | FunctionPointer] | Never],
    ) -> None:
        self.blocks = blocks
        self.block_type_stacks = block_type_stacks
        super().__init__(blocks[0].position)

    def __str__(self) -> str:
        message = "Inconsistent stack types for match cases:\n"

        for block, type_stack in zip(self.blocks, self.block_type_stacks, strict=True):
            description = describe_block(block)

            message += (
                f"{block.position}: ({description}) {format_typestack(type_stack)}\n"
            )

        return message.removesuffix("\n")


class DuplicateCase(TypeCheckerException):
    def __init__(
        self, first: CaseBlock | DefaultBlock, second: CaseBlock | DefaultBlock
    ) -> None:
        self.first = first
        self.second = second

    def __str__(self) -> str:
        return (
            "Duplicate case found in match block:\n"
            + f"{self.first.position}: {describe_block(self.first)}\n"
            + f"{self.second.position}: {describe_block(self.second)}"
        )


class MissingEnumCases(TypeCheckerException):
    def __init__(
        self,
        match_block: MatchBlock,
        enum_type: Enum,
        missing_variants: set[str],
    ) -> None:
        self.match_block = match_block
        self.missing_variants = missing_variants
        self.enum_type = enum_type

    def __str__(self) -> str:
        return (
            f"{self.match_block.position}: Missing cases "
            + f"for enum {self.enum_type.name}.\n"
            + "\n".join(
                [
                    f"- {self.enum_type.name}:{variant}"
                    for variant in self.missing_variants
                ]
            )
        )


class UnreachableDefaultBlock(TypeCheckerException):
    def __init__(self, block: DefaultBlock) -> None:
        self.block = block

    def __str__(self) -> str:
        return f"{self.block.position}: Unreachable default block."


class CaseAsArgumentCountError(TypeCheckerException):
    def __init__(self, case_block: CaseBlock, associated_items: int):
        self.case_block = case_block
        self.associated_items = associated_items

    def __str__(self) -> str:
        expected_args = len(self.case_block.variables)

        return (
            f"{self.case_block.position}: Unexpected number of case-arguments.\n"
            + f"Expected arguments: {expected_args}\n"
            + f"   Found arguments: {self.associated_items}"
        )


class UnknownVariableOrFunction(TypeCheckerException):
    def __init__(self, var_name: str, position: Position) -> None:
        self.name = var_name
        super().__init__(position)

    def __str__(self) -> str:
        return f"{self.position}: Usage of unknown variable or function {self.name}"


class UnsupportedOperator(TypeCheckerException):
    def __init__(self, type_name: str, operator: str, position: Position) -> None:
        self.type_name = type_name
        self.operator = operator
        super().__init__(position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Type {self.type_name} "
            + f"does not support operator {self.operator}"
        )


class CollidingVariable(TypeCheckerException):
    def __init__(
        self,
        lhs: Variable | Argument,
        rhs: Variable | Argument | Struct | Enum | Function,
    ) -> None:
        def sort_key(
            item: Variable | Argument | Struct | Function | Enum,
        ) -> tuple[int, int]:
            return (item.position.line, item.position.column)

        self.colliding = sorted([lhs, rhs], key=sort_key)

    def __str__(self) -> str:
        msg = "Found name collision:\n"

        for item in self.colliding:
            msg += f"{item.position}: {describe(item)}\n"

        return msg.removesuffix("\n")


class InvalidCallWithTypeParameters(TypeCheckerException):
    def __init__(self, call_var: CallVariable, var: Variable | Argument) -> None:
        self.call_var = call_var
        self.var = var
        super().__init__(call_var.position)

    def __str__(self) -> str:
        if isinstance(self.var, Argument):
            object = "argument"
        else:
            assert isinstance(self.var, Variable)
            object = "variable"

        return (
            f"{self.position}: Cannot use {object} {self.call_var.name} "
            + "with type parameters"
        )


class UseFieldOfEnumException(TypeCheckerException):
    def __init__(self, node: StructFieldQuery | StructFieldUpdate) -> None:
        self.node = node
        super().__init__(node.position)

    def __str__(self) -> str:
        if isinstance(self.node, StructFieldQuery):
            get_set = "get"
        else:
            get_set = "set"

        return f"{self.position}: Cannot {get_set} field on Enum"


class UseFieldOfFunctionPointerException(TypeCheckerException):
    def __init__(self, node: StructFieldQuery | StructFieldUpdate) -> None:
        self.node = node
        super().__init__(node.position)

    def __str__(self) -> str:
        if isinstance(self.node, StructFieldQuery):
            get_set = "get"
        else:
            get_set = "set"

        return f"{self.position}: Cannot {get_set} field on FunctionPointer"


class UnexpectedTypeParameterCount(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        expected_param_count: int,
        found_param_count: int,
    ) -> None:
        self.position = position
        self.expected_param_count = expected_param_count
        self.found_param_count = found_param_count
        super().__init__(position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Unexpected number of type parameters\n"
            + f"Expected parameter count: {self.expected_param_count}\n"
            + f"   Found parameter count: {self.found_param_count}"
        )


class SignatureItemMismatch(AaaException):
    """
    Raised when stack doesn't match the signature of a function.
    """

    ...

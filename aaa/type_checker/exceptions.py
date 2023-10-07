from pathlib import Path
from typing import List, Optional, Set, Tuple

from aaa import AaaException, Position
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


def format_typestack(type_stack: List[VariableType | FunctionPointer] | Never) -> str:
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
        computed_return_types: List[VariableType | FunctionPointer] | Never,
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
        type_stack: List[VariableType | FunctionPointer],
        func_like: Function
        | EnumConstructor
        | CallFunctionByPointer
        | StructFieldUpdate
        | StructFieldQuery,
        type_params: List[VariableType | FunctionPointer] = [],
        expected_stack_top_override: Optional[
            List[VariableType | FunctionPointer]
        ] = None,
    ) -> None:
        self.type_stack = type_stack
        self.func_like = func_like
        self.type_params = type_params
        self.expected_stack_top_override = expected_stack_top_override
        super().__init__(position)

    def func_like_name(self) -> str:  # pragma: nocover
        if isinstance(self.func_like, (Function, EnumConstructor)):
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
            f"{self.position}: Invalid stack types when calling {self.func_like_name()}\n"
            + f"Expected stack top: "
            + self.format_expected_typestack()
            + "\n"
            + f"       Found stack: "
            + format_typestack(self.type_stack)
            + "\n"
        )


class ConditionTypeError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: List[VariableType | FunctionPointer],
        condition_stack: List[VariableType | FunctionPointer],
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
        type_stack: List[VariableType | FunctionPointer],
        if_stack: List[VariableType | FunctionPointer],
        else_stack: List[VariableType | FunctionPointer],
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
        type_stack: List[VariableType | FunctionPointer],
        loop_stack: List[VariableType | FunctionPointer],
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
        type_stack: List[VariableType | FunctionPointer],
        type_stack_before: List[VariableType | FunctionPointer],
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
        type_stack: List[VariableType | FunctionPointer],
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
            f"{self.position}: Attempt to set field {self.field_name} of {self.struct_type.name} to wrong type\n"
            + f"Expected type: {self.expected_type}\n"
            + f"   Found type: {self.found_type}\n"
            + "\n"
            + "Type stack: "
            + format_typestack(self.type_stack)
            + "\n"
        )


class InvalidMemberFunctionSignature(TypeCheckerException):
    def __init__(self, function: Function, type: Struct | Enum) -> None:
        self.type = type
        self.function = function
        super().__init__(function.position)

    def __str__(self) -> str:
        full_func_name = f"{self.function.struct_name}:{self.function.func_name}"
        formatted = f"{self.position}: Function {full_func_name} has invalid member-function signature\n\n"

        arguments = [arg.type for arg in self.function.arguments]

        formatted += (
            f"Expected arg types: {self.type.name} ...\n"
            + f"   Found arg types: {' '.join(repr(arg) for arg in arguments)}\n"
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
            + "- returns one value (an iterator)\n"
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
        type_stack: List[VariableType | FunctionPointer],
        foreach_stack: List[VariableType | FunctionPointer],
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
        expected_var_types: List[VariableType | FunctionPointer],
        found_var_types: List[VariableType | FunctionPointer],
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


class UnreachableCode(TypeCheckerException):
    def __str__(self) -> str:
        return f"{self.position}: Found unreachable code.\n"


class ReturnTypesError(TypeCheckerException):
    def __init__(
        self,
        position: Position,
        type_stack: List[VariableType | FunctionPointer],
        function: Function,
    ) -> None:
        self.type_stack = type_stack
        self.function = function
        super().__init__(position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Invalid stack types when returning.\n"
            + f"function returns: {format_typestack(self.function.return_types)}\n"
            + f"     found stack: {format_typestack(self.type_stack)}\n"
        )


class MatchTypeError(TypeCheckerException):
    def __init__(
        self, match_block: MatchBlock, type_stack: List[VariableType | FunctionPointer]
    ) -> None:
        self.match_block = match_block
        self.type_stack = type_stack
        super().__init__(match_block.position)

    def __str__(self) -> str:
        return (
            f"{self.position}: Cannot match on this stack:\n"
            + f"expected stack types: <enum type>\n"
            + f"   found stack types: {format_typestack(self.type_stack)}\n"
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
        return f"{self.position}: Cannot use case for enum {self.found_enum.name} when matching on enum {self.expected_enum.name}\n"


def describe_block(block: CaseBlock | DefaultBlock) -> str:
    if isinstance(block, CaseBlock):
        return f"case {block.enum_type.name}:{block.variant_name}"
    else:
        return "default"


class CaseStackTypeError(TypeCheckerException):
    def __init__(
        self,
        blocks: List[CaseBlock | DefaultBlock],
        block_type_stacks: List[List[VariableType | FunctionPointer] | Never],
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

        return message


class DuplicateCase(TypeCheckerException):
    def __init__(
        self, first: CaseBlock | DefaultBlock, second: CaseBlock | DefaultBlock
    ) -> None:
        self.first = first
        self.second = second

    def __str__(self) -> str:
        return (
            f"Duplicate case found in match block:\n"
            + f"{self.first.position}: {describe_block(self.first)}\n"
            + f"{self.second.position}: {describe_block(self.second)}\n"
        )


class MissingEnumCases(TypeCheckerException):
    def __init__(
        self, match_block: MatchBlock, enum_type: Enum, missing_variants: Set[str]
    ) -> None:
        self.match_block = match_block
        self.missing_variants = missing_variants
        self.enum_type = enum_type

    def __str__(self) -> str:
        return (
            f"{self.match_block.position}: Missing cases for enum {self.enum_type.name}.\n"
            + "\n".join(
                [
                    f"- {self.enum_type.name}:{variant}"
                    for variant in self.missing_variants
                ]
            )
            + "\n"
        )


class UnreachableDefaultBlock(TypeCheckerException):
    def __init__(self, block: DefaultBlock) -> None:
        self.block = block

    def __str__(self) -> str:
        return f"{self.block.position}: Unreachable default block.\n"


class CaseAsArgumentCountError(TypeCheckerException):
    def __init__(self, case_block: CaseBlock, associated_items: int):
        self.case_block = case_block
        self.associated_items = associated_items

    def __str__(self) -> str:
        expected_args = len(self.case_block.variables)

        return (
            f"{self.case_block.position}: Unexpected number of case-arguments.\n"
            + f"Expected arguments: {expected_args}\n"
            + f"   Found arguments: {self.associated_items}\n"
        )


class UnknownVariableOrFunction(TypeCheckerException):
    def __init__(self, var_name: str, position: Position) -> None:
        self.name = var_name
        super().__init__(position)

    def __str__(self) -> str:
        return f"{self.position}: Usage of unknown variable or function {self.name}\n"


class CollidingVariable(TypeCheckerException):
    def __init__(
        self,
        lhs: Variable | Argument,
        rhs: Variable | Argument | Struct | Enum | Function,
    ) -> None:
        def sort_key(
            item: Variable | Argument | Struct | Function | Enum,
        ) -> Tuple[int, int]:
            return (item.position.line, item.position.column)

        self.colliding = sorted([lhs, rhs], key=sort_key)

    def __str__(self) -> str:
        msg = "Found name collision:\n"

        for item in self.colliding:
            msg += f"{item.position}: {describe(item)}\n"

        return msg


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

        return f"{self.position}: Cannot use {object} {self.call_var.name} with type parameters\n"


class UseFieldOfEnumException(TypeCheckerException):
    def __init__(self, node: StructFieldQuery | StructFieldUpdate) -> None:
        self.node = node
        super().__init__(node.position)

    def __str__(self) -> str:
        if isinstance(self.node, StructFieldQuery):
            get_set = "get"
        else:
            get_set = "set"

        return f"{self.position}: Cannot {get_set} field on Enum\n"


class UseFieldOfFunctionPointerException(TypeCheckerException):
    def __init__(self, node: StructFieldQuery | StructFieldUpdate) -> None:
        self.node = node
        super().__init__(node.position)

    def __str__(self) -> str:
        if isinstance(self.node, StructFieldQuery):
            get_set = "get"
        else:
            get_set = "set"

        return f"{self.position}: Cannot {get_set} field on FunctionPointer\n"


class SignatureItemMismatch(AaaException):
    """
    Raised when stack doesn't match the signature of a function.
    """

    ...

from copy import copy
from typing import Callable, Dict, Type

from lang.parse import (
    AaaTreeNode,
    BooleanLiteral,
    Branch,
    Function,
    FunctionBody,
    Identifier,
    IntegerLiteral,
    Loop,
    Operator,
    StringLiteral,
)
from lang.typing.signatures import OPERATOR_SIGNATURES, Signature, SomeType, TypeStack


class TypeChecker:
    def __init__(self, function: Function) -> None:
        self.function = function

        self.type_check_funcs: Dict[
            Type[AaaTreeNode],
            Callable[[AaaTreeNode, TypeStack], TypeStack],
        ] = {
            IntegerLiteral: self.integer_literal_type_check,
            StringLiteral: self.string_literal_type_check,
            BooleanLiteral: self.boolean_literal_type_check,
            Operator: self.operator_type_check,
            Loop: self.loop_type_check,
            Identifier: self.identifier_type_check,
            Branch: self.branch_type_check,
            FunctionBody: self.function_body_type_check,
        }

    def check_types(self) -> None:
        type_stack = [arg.type for arg in self.function.arguments]

        computed_return_types = self.function_body_type_check(self.function, type_stack)
        expected_return_types = [
            return_type.type for return_type in self.function.return_types
        ]

        if computed_return_types != expected_return_types:
            raise NotImplementedError

    def check_and_apply_signature(
        self, type_stack: TypeStack, signature: Signature
    ) -> TypeStack:
        arg_count = len(signature.arg_types)

        if len(type_stack) < arg_count:
            raise NotImplementedError

        type_stack_under_args = type_stack[:-arg_count]
        type_stack_args = type_stack[-arg_count:]

        for arg_type, type_stack_arg in zip(signature.arg_types, type_stack_args):
            if type(arg_type) != type(type_stack_arg) and not isinstance(
                arg_type, SomeType
            ):
                raise NotImplementedError

        # TODO we should replace SomeArg by concrete types here

        returned_types: TypeStack = signature.return_types

        return copy(type_stack_under_args) + returned_types

    def integer_literal_type_check(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        return type_stack + [int]

    def string_literal_type_check(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        return type_stack + [str]

    def boolean_literal_type_check(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        return type_stack + [bool]

    def operator_type_check(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, Operator)
        signatures = OPERATOR_SIGNATURES[node.value]

        # TODO write loop
        assert len(signatures) == 1
        signature = signatures[0]

        return self.check_and_apply_signature(type_stack, signature)

    def loop_type_check(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        # TODO use copy on type_stack before checking children
        raise NotImplementedError

    def identifier_type_check(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        # TODO use copy on type_stack before checking children
        raise NotImplementedError

    def branch_type_check(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        # TODO use copy on type_stack before checking children
        raise NotImplementedError

    def function_body_type_check(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        # TODO use copy on type_stack before checking children
        raise NotImplementedError

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
from lang.typing.exceptions import (
    FunctionTypeError,
    StackTypesError,
    StackUnderflowError,
)
from lang.typing.signatures import (
    OPERATOR_SIGNATURES,
    PlaceholderType,
    Signature,
    SignatureItem,
    TypeStack,
)


class TypeChecker:
    def __init__(self, function: Function) -> None:
        self.function = function

        self.type_check_funcs: Dict[
            Type[AaaTreeNode],
            Callable[[AaaTreeNode, TypeStack], TypeStack],
        ] = {
            IntegerLiteral: self._check_integer_literal,
            StringLiteral: self.check_string_literal,
            BooleanLiteral: self._check_boolean_literal,
            Operator: self._check_operator,
            Loop: self._check_loop,
            Identifier: self._check_identifier,
            Branch: self._check_branch,
            FunctionBody: self._check_function_body,
            Function: self._check_function,
        }

    def check(self) -> None:
        computed_return_types = self._check(self.function, [])
        expected_return_types = [
            return_type.type for return_type in self.function.return_types
        ]

        if computed_return_types != expected_return_types:
            raise FunctionTypeError

    def _check(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        return self.type_check_funcs[type(node)](node, type_stack)

    def _check_and_apply_signature(
        self, type_stack: TypeStack, signature: Signature
    ) -> TypeStack:
        stack = copy(type_stack)

        arg_count = len(signature.arg_types)

        if len(stack) < arg_count:
            raise StackUnderflowError

        if arg_count == 0:
            type_stack_under_args = stack
            type_stack_args = []
        else:
            type_stack_under_args = stack[:-arg_count]
            type_stack_args = stack[-arg_count:]

        placeholder_types: Dict[str, SignatureItem] = {}

        for signature_arg_type, type_stack_arg in zip(
            signature.arg_types, type_stack_args, strict=True
        ):
            if isinstance(signature_arg_type, PlaceholderType):
                placeholder_types[signature_arg_type.name] = type_stack_arg
            elif signature_arg_type != type_stack_arg:
                raise StackTypesError

        stack = type_stack_under_args

        for return_type in signature.return_types:
            if isinstance(return_type, PlaceholderType):
                stack.append(placeholder_types[return_type.name])
            else:
                stack.append(return_type)

        return stack

    def _check_integer_literal(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        return type_stack + [int]

    def check_string_literal(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        return type_stack + [str]

    def _check_boolean_literal(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        return type_stack + [bool]

    def _check_operator(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        assert isinstance(node, Operator)
        signatures = OPERATOR_SIGNATURES[node.value]

        # TODO write loop
        assert len(signatures) == 1
        signature = signatures[0]

        return self._check_and_apply_signature(type_stack, signature)

    def _check_loop(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        # TODO use copy on type_stack before checking children
        raise NotImplementedError

    def _check_identifier(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        # TODO use copy on type_stack before checking children
        raise NotImplementedError

    def _check_branch(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        # TODO use copy on type_stack before checking children
        raise NotImplementedError

    def _check_function_body(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, FunctionBody)

        stack = copy(type_stack)
        for function_body_item in node.items:
            stack = self._check(function_body_item, copy(stack))

        return stack

    def _check_function(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        assert isinstance(node, Function)
        # TODO put special type rules if name == main

        return self._check(node.body, type_stack)

from copy import copy
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, Optional, Set, Type

from lang.parse import (
    AaaTreeNode,
    BooleanLiteral,
    Branch,
    File,
    Function,
    FunctionBody,
    Identifier,
    IntegerLiteral,
    Loop,
    Operator,
    StringLiteral,
)

if TYPE_CHECKING:
    from lang.program import Program

from lang.typing.exceptions import (
    FunctionTypeError,
    StackTypesError,
    StackUnderflowError,
    UnknownPlaceholderTypes,
)
from lang.typing.signatures import (
    OPERATOR_SIGNATURES,
    PlaceholderType,
    Signature,
    SignatureItem,
    TypeStack,
)


class TypeChecker:
    def __init__(self, file: Path, parsed_file: File, program: "Program") -> None:
        self.parsed_file = parsed_file
        self.program = program
        self.file = file

        self.type_check_funcs: Dict[
            Type[AaaTreeNode],
            Callable[[AaaTreeNode, Function, TypeStack], TypeStack],
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
        for func_name, function in self.parsed_file.functions.items():
            computed_return_types = self._check(function, function, [])
            expected_return_types = function.get_signature().return_types

            if computed_return_types != expected_return_types:
                raise FunctionTypeError

    def _get_func_arg_type(
        self, function: Function, name: str
    ) -> Optional[SignatureItem]:
        for arg in function.arguments:
            if arg.name == name:
                return arg.type
        return None

    def _check(
        self, node: AaaTreeNode, function: Function, type_stack: TypeStack
    ) -> TypeStack:
        return self.type_check_funcs[type(node)](node, function, type_stack)

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
        self, node: AaaTreeNode, function: Function, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, IntegerLiteral)
        return type_stack + [int]

    def check_string_literal(
        self, node: AaaTreeNode, function: Function, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, StringLiteral)
        return type_stack + [str]

    def _check_boolean_literal(
        self, node: AaaTreeNode, function: Function, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, BooleanLiteral)
        return type_stack + [bool]

    def _check_operator(
        self, node: AaaTreeNode, function: Function, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, Operator)
        signatures = OPERATOR_SIGNATURES[node.value]

        stack: Optional[TypeStack] = None

        for signature in signatures:
            try:
                stack = self._check_and_apply_signature(copy(type_stack), signature)
                break
            except StackTypesError:
                pass

        if stack is None:
            raise StackTypesError

        return stack

    def _check_branch(
        self, node: AaaTreeNode, function: Function, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, Branch)
        # Condition should push exactly one boolean and nothing else.
        condition_stack = self._check(node.condition, function, copy(type_stack))

        if not all(
            [
                len(condition_stack) == len(type_stack) + 1,
                condition_stack[:-1] == type_stack,
                condition_stack[-1] == bool,
            ]
        ):
            raise StackTypesError

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for both the if- and else- bodies.
        if_stack = self._check(node.if_body, function, copy(type_stack))
        else_stack = self._check(node.else_body, function, copy(type_stack))

        # Regardless whether the if- or else- branch is taken,
        # afterwards the stack should be the same.
        if if_stack != else_stack:
            raise StackTypesError

        # we can return either one, since they are the same
        return if_stack

    def _check_loop(
        self, node: AaaTreeNode, function: Function, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, Loop)
        # Condition should push exactly one boolean and nothing else.
        condition_stack = self._check(node.condition, function, copy(type_stack))

        if not all(
            [
                len(condition_stack) == len(type_stack) + 1,
                condition_stack[:-1] == type_stack,
                condition_stack[-1] == bool,
            ]
        ):
            raise StackTypesError

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for the loop body.
        loop_stack = self._check(node.body, function, copy(type_stack))

        if loop_stack != type_stack:
            raise StackTypesError

        # we can return either one, since they are the same
        return loop_stack

    def _check_identifier(
        self, node: AaaTreeNode, function: Function, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, Identifier)
        # If it's a function argument, just push the type.
        arg_type = self._get_func_arg_type(function, node.name)

        if arg_type is not None:
            return copy(type_stack) + [arg_type]

        # If it's not a function argument, we are calling a function.

        try:
            func = self.parsed_file.functions[node.name]
        except KeyError:
            pass
        else:
            signature = func.get_signature()
            return self._check_and_apply_signature(copy(type_stack), signature)

        # Either the called function exists in a different file
        # or it doesn't exist at all. This is not implemented yet.
        raise NotImplementedError

    def _check_function_body(
        self, node: AaaTreeNode, function: Function, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, FunctionBody)

        stack = copy(type_stack)
        for function_body_item in node.items:
            stack = self._check(function_body_item, function, copy(stack))

        return stack

    def _check_function(
        self, node: AaaTreeNode, function: Function, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, Function)

        placeholder_arg_types: Set[str] = set()
        placeholder_return_types: Set[str] = set()

        for arg in function.arguments:
            if isinstance(arg.type, PlaceholderType):
                placeholder_arg_types.add(arg.type.name)

        for return_arg in function.return_types:
            if isinstance(return_arg.type, PlaceholderType):
                placeholder_return_types.add(return_arg.type.name)

        unknown_return_types = placeholder_return_types - placeholder_arg_types

        if unknown_return_types:
            raise UnknownPlaceholderTypes(unknown_return_types)

        # TODO put special type rules if name == main

        return self._check(node.body, function, type_stack)

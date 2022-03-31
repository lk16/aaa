from copy import copy
from parser.tokenizer.models import Token
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Set, Type

from lang.runtime.parse import (
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

if TYPE_CHECKING:  # pragma: nocover
    from lang.runtime.program import Program

from lang.typing.exceptions import (
    ArgumentNameCollision,
    BranchTypeError,
    ConditionTypeError,
    FunctionTypeError,
    InvalidMainSignuture,
    LoopTypeError,
    StackTypesError,
    StackUnderflowError,
    UnknownFunction,
    UnknownPlaceholderType,
    UnknownType,
)
from lang.typing.signatures import (
    IDENTIFIER_TO_TYPE,
    OPERATOR_SIGNATURES,
    PlaceholderType,
    Signature,
    SignatureItem,
    TypeStack,
)


class TypeChecker:
    def __init__(
        self,
        file: Path,
        function: Function,
        tokens: List[Token],
        program: "Program",
    ) -> None:
        self.function = function
        self.program = program
        self.file = file
        self.tokens = tokens

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
        expected_return_types = self._get_function_signature(self.function).return_types

        if computed_return_types != expected_return_types:
            raise FunctionTypeError(
                self.file,
                self.function,
                self.tokens,
                expected_return_types,
                computed_return_types,
            )

    # TODO move this function to Program
    def _string_to_signature_item(
        self, placeholder_name: str, type: str, node: AaaTreeNode
    ) -> SignatureItem:
        if type.startswith("*"):
            return PlaceholderType(placeholder_name)

        try:
            return IDENTIFIER_TO_TYPE[type]
        except KeyError as e:
            # TODO change grammar so we can point the error to token of type rather than name of the arg
            raise UnknownType(self.file, self.function, self.tokens, node) from e

    def _get_function_signature(self, function: Function) -> Signature:
        placeholder_args: Set[str] = {
            arg_type.type
            for arg_type in function.arguments
            if arg_type.type.startswith("*")
        }

        for return_type in function.return_types:
            if (
                return_type.type.startswith("*")
                and return_type.type not in placeholder_args
            ):
                raise UnknownPlaceholderType(
                    self.file, self.function, self.tokens, return_type
                )

        arg_types: List[SignatureItem] = []
        for arg_type in function.arguments:
            sig_item = self._string_to_signature_item(
                arg_type.name, arg_type.type, arg_type
            )
            arg_types.append(sig_item)

        return_types: List[SignatureItem] = []
        for return_type in function.return_types:
            placeholder_name = return_type.type[1:]
            sig_item = self._string_to_signature_item(
                placeholder_name, return_type.type, return_type
            )
            return_types.append(sig_item)

        return Signature(arg_types, return_types)

    def _get_func_arg_type(self, name: str) -> Optional[SignatureItem]:
        for arg in self.function.arguments:
            if arg.name == name:
                if arg.type.startswith("*"):
                    return PlaceholderType(arg.name)
                return IDENTIFIER_TO_TYPE[arg.type]
        return None

    def _check(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        return self.type_check_funcs[type(node)](node, type_stack)

    def _check_and_apply_signature(
        self, type_stack: TypeStack, signature: Signature, node: AaaTreeNode
    ) -> TypeStack:
        stack = copy(type_stack)

        arg_count = len(signature.arg_types)

        if len(stack) < arg_count:
            raise StackUnderflowError(self.file, self.function, self.tokens, node)

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
                raise StackTypesError(
                    self.file, self.function, self.tokens, node, signature, type_stack
                )

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
        assert isinstance(node, IntegerLiteral)
        return type_stack + [int]

    def check_string_literal(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, StringLiteral)
        return type_stack + [str]

    def _check_boolean_literal(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, BooleanLiteral)
        return type_stack + [bool]

    def _check_operator(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        assert isinstance(node, Operator)
        signatures = OPERATOR_SIGNATURES[node.value]

        stack: Optional[TypeStack] = None
        last_stack_type_error: Optional[StackTypesError] = None

        for signature in signatures:
            try:
                stack = self._check_and_apply_signature(
                    copy(type_stack), signature, node
                )
                break
            except StackTypesError as e:
                last_stack_type_error = e

        if stack is None:
            assert last_stack_type_error
            raise last_stack_type_error

        return stack

    def _check_branch(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        assert isinstance(node, Branch)
        # Condition should push exactly one boolean and nothing else.
        condition_stack = self._check(node.condition, copy(type_stack))

        if not all(
            [
                len(condition_stack) == len(type_stack) + 1,
                condition_stack[:-1] == type_stack,
                condition_stack[-1] == bool,
            ]
        ):
            raise ConditionTypeError(
                self.file, self.function, self.tokens, node, type_stack, condition_stack
            )

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for both the if- and else- bodies.
        if_stack = self._check(node.if_body, copy(type_stack))
        else_stack = self._check(node.else_body, copy(type_stack))

        # Regardless whether the if- or else- branch is taken,
        # afterwards the stack should be the same.
        if if_stack != else_stack:
            raise BranchTypeError(
                self.file,
                self.function,
                self.tokens,
                node,
                type_stack,
                if_stack,
                else_stack,
            )

        # we can return either one, since they are the same
        return if_stack

    def _check_loop(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        assert isinstance(node, Loop)
        # Condition should push exactly one boolean and nothing else.
        condition_stack = self._check(node.condition, copy(type_stack))

        if not all(
            [
                len(condition_stack) == len(type_stack) + 1,
                condition_stack[:-1] == type_stack,
                condition_stack[-1] == bool,
            ]
        ):
            raise ConditionTypeError(
                self.file, self.function, self.tokens, node, type_stack, condition_stack
            )

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for the loop body.
        loop_stack = self._check(node.body, copy(type_stack))

        if loop_stack != type_stack:
            raise LoopTypeError(
                self.file, self.function, self.tokens, node, type_stack, loop_stack
            )

        # we can return either one, since they are the same
        return loop_stack

    def _check_identifier(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        assert isinstance(node, Identifier)
        # If it's a function argument, just push the type.
        arg_type = self._get_func_arg_type(node.name)

        if arg_type is not None:
            return copy(type_stack) + [arg_type]

        # If it's not a function argument, we must be calling a function.
        func = self.program.get_function(node.name)

        if not func:
            raise UnknownFunction(self.file, self.function, self.tokens, node)

        signature = self._get_function_signature(func)
        return self._check_and_apply_signature(copy(type_stack), signature, node)

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

        if node.name == "main":
            if not all(
                [
                    len(node.arguments) == 0,
                    len(node.return_types) == 0,
                ]
            ):
                raise InvalidMainSignuture(self.file, self.function, self.tokens, node)

        argument_and_names: Set[str] = set()

        for arg in node.arguments:
            if arg.name in argument_and_names or node.name == arg.name:
                raise ArgumentNameCollision(self.file, self.function, self.tokens, arg)
            argument_and_names.add(arg.name)

        # TODO put special type rules if name == main

        return self._check(node.body, type_stack)

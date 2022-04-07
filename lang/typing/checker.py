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
    ParsedTypePlaceholder,
    StringLiteral,
    TypeLiteral,
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
)
from lang.typing.signatures import OPERATOR_SIGNATURES
from lang.typing.types import (
    Bool,
    Int,
    PlaceholderType,
    RootType,
    Signature,
    SignatureItem,
    Str,
    TypeStack,
    VariableType,
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
            BooleanLiteral: self._check_boolean_literal,
            Branch: self._check_branch,
            Function: self._check_function,
            FunctionBody: self._check_function_body,
            Identifier: self._check_identifier,
            IntegerLiteral: self._check_integer_literal,
            Loop: self._check_loop,
            Operator: self._check_operator,
            StringLiteral: self.check_string_literal,
            TypeLiteral: self._check_type_literal,
        }

    def check(self) -> None:
        computed_return_types = self._check(self.function, [])
        expected_return_types = self._get_function_signature(self.function).return_types

        if computed_return_types != expected_return_types:
            raise FunctionTypeError(
                file=self.file,
                tokens=self.tokens,
                function=self.function,
                expected_return_types=expected_return_types,
                computed_return_types=computed_return_types,
            )

    def _get_function_signature(self, function: Function) -> Signature:
        placeholder_args: Set[str] = set()

        for argument in function.arguments:
            if isinstance(argument.type, ParsedTypePlaceholder):
                placeholder_args.add(argument.type.name)

        for return_type in function.return_types:
            if (
                isinstance(return_type.type, ParsedTypePlaceholder)
                and return_type.type.name not in placeholder_args
            ):
                raise UnknownPlaceholderType(
                    file=self.file,
                    function=self.function,
                    tokens=self.tokens,
                    node=return_type,
                )

        arg_types: List[SignatureItem] = []
        return_types: List[SignatureItem] = []

        for argument in function.arguments:
            if isinstance(argument.type, PlaceholderType):
                arg_types.append(argument.type)
            elif isinstance(argument.type, TypeLiteral):
                arg_types.append(VariableType.from_type_literal(argument.type))
            else:  # pragma: nocover
                assert False

        for return_type in function.return_types:
            if isinstance(return_type.type, PlaceholderType):
                return_types.append(return_type.type)
            elif isinstance(return_type.type, TypeLiteral):
                return_types.append(VariableType.from_type_literal(return_type.type))
            else:  # pragma: nocover
                assert False

        return Signature(arg_types, return_types)

    def _get_func_arg_type(self, name: str) -> Optional[SignatureItem]:
        for argument in self.function.arguments:
            if argument.name == name:
                if isinstance(argument, PlaceholderType):
                    return argument
                elif isinstance(argument, TypeLiteral):
                    return VariableType.from_type_literal(argument)

        return None

    def _check(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        return self.type_check_funcs[type(node)](node, type_stack)

    def _check_and_apply_signature(
        self, type_stack: TypeStack, signature: Signature, node: AaaTreeNode
    ) -> TypeStack:
        stack = copy(type_stack)

        arg_count = len(signature.arg_types)

        if len(stack) < arg_count:
            raise StackUnderflowError(
                file=self.file, function=self.function, tokens=self.tokens, node=node
            )

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
            if isinstance(signature_arg_type, ParsedTypePlaceholder):
                placeholder_types[signature_arg_type.name] = type_stack_arg
            elif signature_arg_type != type_stack_arg:
                raise StackTypesError(
                    file=self.file,
                    function=self.function,
                    tokens=self.tokens,
                    node=node,
                    signature=signature,
                    type_stack=type_stack,
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
        return type_stack + [Int]

    def check_string_literal(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, StringLiteral)
        return type_stack + [Str]

    def _check_boolean_literal(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, BooleanLiteral)
        return type_stack + [Bool]

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

    def _check_type_literal(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, TypeLiteral)

        # TODO we need to convert TypeLiteral into a VariableType instance
        if node.type_name == "int":
            return type_stack + [Int]
        if node.type_name == "str":
            return type_stack + [Str]
        if node.type_name == "bool":
            return type_stack + [Bool]

        raise NotImplementedError

    def _check_branch(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        assert isinstance(node, Branch)

        # TODO move condition check to new function and call also from _check_loop
        # Condition should push exactly one boolean and nothing else.
        condition_stack = self._check(node.condition, copy(type_stack))

        if not (
            len(condition_stack) == len(type_stack) + 1
            and condition_stack[:-1] == type_stack
            and isinstance(condition_stack[-1], VariableType)
            and condition_stack[-1].root_type == RootType.BOOL
        ):
            raise ConditionTypeError(
                file=self.file,
                function=self.function,
                tokens=self.tokens,
                node=node,
                type_stack=type_stack,
                condition_stack=condition_stack,
            )

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for both the if- and else- bodies.
        if_stack = self._check(node.if_body, copy(type_stack))
        else_stack = self._check(node.else_body, copy(type_stack))

        # Regardless whether the if- or else- branch is taken,
        # afterwards the stack should be the same.
        if if_stack != else_stack:
            raise BranchTypeError(
                file=self.file,
                function=self.function,
                tokens=self.tokens,
                node=node,
                type_stack=type_stack,
                if_stack=if_stack,
                else_stack=else_stack,
            )

        # we can return either one, since they are the same
        return if_stack

    def _check_loop(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        assert isinstance(node, Loop)
        # Condition should push exactly one boolean and nothing else.
        condition_stack = self._check(node.condition, copy(type_stack))

        if not (
            len(condition_stack) == len(type_stack) + 1
            and condition_stack[:-1] == type_stack
            and isinstance(condition_stack[-1], VariableType)
            and condition_stack[-1].root_type == RootType.BOOL
        ):
            raise ConditionTypeError(
                file=self.file,
                function=self.function,
                tokens=self.tokens,
                node=node,
                type_stack=type_stack,
                condition_stack=condition_stack,
            )

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for the loop body.
        loop_stack = self._check(node.body, copy(type_stack))

        if loop_stack != type_stack:
            raise LoopTypeError(
                file=self.file,
                function=self.function,
                tokens=self.tokens,
                node=node,
                type_stack=type_stack,
                loop_stack=loop_stack,
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
        func = self.program.get_function(self.file, node.name)

        if not func:
            raise UnknownFunction(
                file=self.file, function=self.function, tokens=self.tokens, node=node
            )

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
                raise InvalidMainSignuture(
                    file=self.file,
                    function=self.function,
                    tokens=self.tokens,
                    node=node,
                )

        argument_and_names: Set[str] = set()

        for arg in node.arguments:
            if arg.name in argument_and_names or node.name == arg.name:
                raise ArgumentNameCollision(
                    file=self.file, function=self.function, tokens=self.tokens, node=arg
                )
            argument_and_names.add(arg.name)

        return self._check(node.body, type_stack)

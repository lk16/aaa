from copy import copy, deepcopy
from parser.tokenizer.models import Token
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from lang.runtime.parse import (
    AaaTreeNode,
    BooleanLiteral,
    Branch,
    Function,
    FunctionBody,
    Identifier,
    IntegerLiteral,
    Loop,
    MemberFunction,
    Operator,
    ParsedType,
    ParsedTypePlaceholder,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    TypeLiteral,
)

if TYPE_CHECKING:  # pragma: nocover
    from lang.runtime.program import Program

from lang.typing.exceptions import (
    ArgumentNameCollision,
    BranchTypeError,
    ConditionTypeError,
    FunctionTypeError,
    GetFieldOfNonStructTypeError,
    InvalidMainSignuture,
    LoopTypeError,
    SetFieldOfNonStructTypeError,
    StackTypesError,
    StackUnderflowError,
    StructUpdateTypeError,
    UnknownFunction,
    UnknownPlaceholderType,
    UnknownStructField,
)
from lang.typing.types import (
    Bool,
    Int,
    RootType,
    Signature,
    SignatureItem,
    Str,
    TypePlaceholder,
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

    def check(self) -> None:
        computed_return_types = self._check_function(self.function, [])
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
        # TODO consider moving this entire function to Program

        # TODO cache result of calling this function

        placeholder_args: Set[str] = set()

        for argument in function.arguments:
            if isinstance(argument.type.type, ParsedTypePlaceholder):
                placeholder_args.add(argument.type.type.name)

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

        # TODO more and better validation

        return Signature.from_function(function)

    def _get_func_arg_type(self, name: str) -> Optional[SignatureItem]:
        for argument in self.function.arguments:
            type = argument.type.type
            if isinstance(type, ParsedTypePlaceholder):
                if type.name == name:
                    return TypePlaceholder(type.name)
            elif isinstance(type, TypeLiteral):
                if argument.name == name:
                    return VariableType.from_type_literal(type)
            else:  # pragma: nocover
                assert False

        return None

    def _check_and_apply_signature(
        self, type_stack: TypeStack, signature: Signature, node: AaaTreeNode
    ) -> TypeStack:
        stack = copy(type_stack)

        arg_count = len(signature.arg_types)

        if len(stack) < arg_count:
            raise StackUnderflowError(
                file=self.file, function=self.function, tokens=self.tokens, node=node
            )

        placeholder_types: Dict[str, SignatureItem] = {}
        expected_types = signature.arg_types
        types = stack[len(stack) - arg_count :]

        for expected_type, type in zip(expected_types, types, strict=True):
            match_result = self._match_signature_items(
                expected_type, type, placeholder_types
            )

            if not match_result:
                raise StackTypesError(
                    file=self.file,
                    function=self.function,
                    tokens=self.tokens,
                    node=node,
                    signature=signature,
                    type_stack=type_stack,
                )

        stack = stack[: len(stack) - arg_count]

        for return_type in signature.return_types:
            stack.append(
                self._update_return_type(deepcopy(return_type), placeholder_types)
            )

        return stack

    def _match_signature_items(
        self,
        expected_type: SignatureItem,
        type: SignatureItem,
        placeholder_types: Dict[str, SignatureItem],
    ) -> bool:
        if isinstance(expected_type, TypePlaceholder):
            if expected_type.name in placeholder_types:
                return placeholder_types[expected_type.name] == type

            placeholder_types[expected_type.name] = type
            return True

        elif isinstance(expected_type, VariableType):
            if isinstance(type, TypePlaceholder):
                return False

            if expected_type.root_type != type.root_type:
                return False

            if len(type.type_params) != len(expected_type.type_params):
                return False

            for expected_param, param in zip(
                expected_type.type_params, type.type_params
            ):
                match_result = self._match_signature_items(
                    expected_param,
                    param,
                    placeholder_types,
                )

                if not match_result:
                    return False

            return True

        else:  # pragma: nocover
            assert False

    def _update_return_type(
        self, return_type: SignatureItem, placeholder_types: Dict[str, SignatureItem]
    ) -> SignatureItem:
        if isinstance(return_type, TypePlaceholder):
            if return_type.name in placeholder_types:
                return placeholder_types[return_type.name]

            # TODO is this an error?
            return return_type

        elif isinstance(return_type, VariableType):
            for i, param in enumerate(return_type.type_params):
                return_type.type_params[i] = self._update_return_type(
                    param, placeholder_types
                )

            return return_type

        else:  # pragma: nocover
            assert False

    def _check_integer_literal(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, IntegerLiteral)
        return type_stack + [Int]

    def _check_string_literal(
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

        signatures = self.program._builtins.functions[node.value]

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

        type = VariableType.from_type_literal(node)
        return type_stack + [type]

    def _check_condition(self, node: AaaTreeNode, type_stack: TypeStack) -> None:
        assert isinstance(node, FunctionBody)

        # Condition is a special type of function body:
        # It should push exactly one boolean and not modify the type stack under it
        condition_stack = self._check_function_body(node, copy(type_stack))

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

    def _check_branch(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        assert isinstance(node, Branch)

        self._check_condition(node.condition, copy(type_stack))

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for both the if- and else- bodies.
        if_stack = self._check_function_body(node.if_body, copy(type_stack))
        else_stack = self._check_function_body(node.else_body, copy(type_stack))

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

        self._check_condition(node.condition, copy(type_stack))

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for the loop body.
        loop_stack = self._check_function_body(node.body, copy(type_stack))

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
        identifier = self.program.get_identifier(self.file, node.name)

        if not identifier:
            # TODO rename to UnknownIdentifier
            raise UnknownFunction(
                file=self.file, function=self.function, tokens=self.tokens, node=node
            )

        if isinstance(identifier, Function):
            signature = self._get_function_signature(identifier)
            return self._check_and_apply_signature(copy(type_stack), signature, node)

        elif isinstance(identifier, Struct):
            return copy(type_stack) + [
                VariableType(RootType.STRUCT, struct_name=identifier.name)
            ]

        else:
            assert False

    def _check_function_body(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, FunctionBody)

        stack = copy(type_stack)
        for child_node in node.items:
            if isinstance(child_node, BooleanLiteral):
                stack = self._check_boolean_literal(child_node, copy(stack))
            elif isinstance(child_node, Branch):
                stack = self._check_branch(child_node, copy(stack))
            elif isinstance(child_node, Identifier):
                stack = self._check_identifier(child_node, copy(stack))
            elif isinstance(child_node, IntegerLiteral):
                stack = self._check_integer_literal(child_node, copy(stack))
            elif isinstance(child_node, Loop):
                stack = self._check_loop(child_node, copy(stack))
            elif isinstance(child_node, MemberFunction):
                stack = self._check_member_function_call(child_node, copy(stack))
            elif isinstance(child_node, Operator):
                stack = self._check_operator(child_node, copy(stack))
            elif isinstance(child_node, StringLiteral):
                stack = self._check_string_literal(child_node, copy(stack))
            elif isinstance(child_node, TypeLiteral):
                stack = self._check_type_literal(child_node, copy(stack))
            elif isinstance(child_node, StructFieldQuery):
                stack = self._check_type_struct_field_query(child_node, copy(stack))
            elif isinstance(child_node, StructFieldUpdate):
                stack = self._check_type_struct_field_update(child_node, copy(stack))
            else:  # pragma nocover
                assert False

        return stack

    def _check_member_function_call(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, MemberFunction)

        # TODO check that first argument is the type we operate on

        # TODO check that first return value is type type we operate on

        # TODO handle methods on user-created types

        key = f"{node.type_name}:{node.func_name}"

        # All builtin member functions should be listed in the builtins file
        # so this should not raise a KeyError.
        signatures = self.program._builtins.functions[key]

        # All builtin member functions should have a unique signature
        assert len(signatures) == 1

        return self._check_and_apply_signature(type_stack, signatures[0], node)

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

        return self._check_function_body(node.body, type_stack)

    def _get_struct_field_type(
        self, node: StructFieldQuery | StructFieldUpdate, struct: Struct
    ) -> VariableType:
        # TODO consider moving this out since it doesn't use self

        field_type: Optional[ParsedType] = None
        field_name = node.field_name.value

        for field in struct.fields:
            if field.name == field_name:
                field_type = field.type
                break

        if not field_type:
            raise UnknownStructField(
                file=self.file,
                tokens=self.tokens,
                node=node,
                function=self.function,
                struct=struct,
                field_name=field_name,
            )

        assert isinstance(field_type.type, TypeLiteral)
        return VariableType.from_type_literal(field_type.type)

    def _check_type_struct_field_query(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, StructFieldQuery)

        type_stack = self._check_string_literal(node.field_name, copy(type_stack))

        if len(type_stack) < 2:
            raise StackUnderflowError(
                file=self.file, function=self.function, tokens=self.tokens, node=node
            )

        struct_type, field_selector_type = type_stack[-2:]

        assert isinstance(struct_type, VariableType)
        assert isinstance(field_selector_type, VariableType)

        # This is enforced by the parser
        assert field_selector_type.root_type == RootType.STRING

        if struct_type.root_type != RootType.STRUCT:
            raise GetFieldOfNonStructTypeError(
                file=self.file,
                tokens=self.tokens,
                node=node,  # TODO point to the actual '?' in the printed error message
                type_stack=type_stack,
                function=self.function,
            )

        struct_name = struct_type.struct_name

        # These should not raise, they are enforced by the Program class
        struct = self.program.identifiers[self.file][struct_name]
        assert isinstance(struct, Struct)

        field_type = self._get_struct_field_type(node, struct)

        type_stack.pop()
        type_stack.append(field_type)
        return type_stack

    def _check_type_struct_field_update(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, StructFieldUpdate)
        type_stack = self._check_string_literal(node.field_name, copy(type_stack))

        type_stack_before = type_stack
        type_stack = self._check_function_body(
            node.new_value_expr, copy(type_stack_before)
        )

        if len(type_stack) < 3:
            raise StackUnderflowError(
                file=self.file, function=self.function, tokens=self.tokens, node=node
            )

        struct_type, field_selector_type, update_expr_type = type_stack[-3:]

        assert isinstance(struct_type, VariableType)
        assert isinstance(field_selector_type, VariableType)
        assert isinstance(update_expr_type, VariableType)

        if not all(
            [
                len(type_stack_before) == len(type_stack) - 1,
                type_stack_before == type_stack[:-1],
            ]
        ):
            raise StructUpdateTypeError(
                file=self.file,
                function=self.function,
                tokens=self.tokens,
                node=node,
                type_stack=type_stack,
                type_stack_before=type_stack_before,
            )

        struct_name = struct_type.struct_name

        if struct_type.root_type != RootType.STRUCT:
            raise SetFieldOfNonStructTypeError(
                file=self.file,
                tokens=self.tokens,
                node=node,  # TODO point to the actual '!' in the printed error message
                type_stack=type_stack,
                function=self.function,
            )

        # These should not raise, they are enforced by the Program class
        struct = self.program.identifiers[self.file][struct_name]
        assert isinstance(struct, Struct)

        field_type = self._get_struct_field_type(node, struct)

        if field_type != update_expr_type:
            raise NotImplementedError

        # drop field_selector and update value
        return type_stack[:-2]

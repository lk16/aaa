from copy import copy, deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Union

from lang.models.parse import (
    AaaTreeNode,
    BooleanLiteral,
    Branch,
    BuiltinFunction,
    Function,
    FunctionBody,
    Identifier,
    IntegerLiteral,
    Loop,
    MemberFunctionName,
    Operator,
    ParsedType,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
)

if TYPE_CHECKING:  # pragma: nocover
    from lang.runtime.program import Program

from lang.exceptions.naming import (
    CollidingIdentifier,
    UnknownArgumentType,
    UnknownIdentifier,
    UnknownPlaceholderType,
    UnknownStructField,
)
from lang.exceptions.typing import (
    BranchTypeError,
    ConditionTypeError,
    FunctionTypeError,
    GetFieldOfNonStructTypeError,
    InvalidMainSignuture,
    InvalidMemberFunctionSignature,
    LoopTypeError,
    SetFieldOfNonStructTypeError,
    StackTypesError,
    StructUpdateStackError,
    StructUpdateTypeError,
)
from lang.typing.types import (
    Bool,
    Int,
    RootType,
    Signature,
    Str,
    StructQuerySignature,
    StructUpdateSignature,
    VariableType,
)


class TypeChecker:
    def __init__(
        self,
        file: Path,
        function: Function,
        program: "Program",
    ) -> None:
        self.function = function
        self.program = program
        self.file = file

    def check(self) -> None:
        self._check_argument_types()
        computed_return_types = self._check_function(self.function, [])
        expected_return_types = self._get_function_signature(self.function).return_types

        if computed_return_types != expected_return_types:

            raise FunctionTypeError(
                file=self.file,
                function=self.function,
                expected_return_types=expected_return_types,
                computed_return_types=computed_return_types,
            )

    def _check_argument_types(self) -> None:

        known_identifiers = self.program.identifiers[self.file]

        for argument in self.function.arguments:
            if argument.type.is_placeholder:
                continue

            arg_type_name = argument.type.name

            # TODO load list from builtin types from builtins.aaa
            if arg_type_name in ["bool", "int", "map", "str", "vec"]:
                return

            if arg_type_name not in known_identifiers:
                raise UnknownArgumentType(
                    file=self.file,
                    function=self.function,
                    parsed_type=argument.type,
                )

            if not isinstance(known_identifiers[arg_type_name], Struct):
                # Identifier was found, but it's not for a struct
                raise UnknownArgumentType(
                    file=self.file,
                    function=self.function,
                    parsed_type=argument.type,
                )

    def _get_function_signature(self, function: Function) -> Signature:
        # TODO consider moving this entire function to Program

        # TODO cache result of calling this function

        placeholder_args: Set[str] = set()

        for argument in function.arguments:
            if argument.type.is_placeholder:
                placeholder_args.add(argument.type.name)

        for return_type in function.return_types:
            if return_type.is_placeholder and return_type.name not in placeholder_args:
                raise UnknownPlaceholderType(
                    file=self.file,
                    function=self.function,
                    parsed_type=return_type,
                )

        # TODO more and better validation

        return Signature.from_function(function)

    def _get_func_arg_type(self, name: str) -> Optional[VariableType]:
        for argument in self.function.arguments:
            if (argument.type.is_placeholder and argument.type.name == name) or (
                not argument.type.is_placeholder and argument.name == name
            ):
                return VariableType.from_parsed_type(argument.type)

        return None

    def _check_and_apply_signature(
        self,
        type_stack: List[VariableType],
        signature: Signature,
        func_like: Union[Operator, Function, MemberFunctionName, BuiltinFunction],
    ) -> List[VariableType]:
        # TODO load signature here, instead of passing it as argument

        stack = copy(type_stack)

        arg_count = len(signature.arg_types)

        if len(stack) < arg_count:
            raise StackTypesError(
                file=self.file,
                function=self.function,
                signature=signature,
                type_stack=type_stack,
                func_like=func_like,
            )

        placeholder_types: Dict[str, VariableType] = {}
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
                    signature=signature,
                    type_stack=type_stack,
                    func_like=func_like,
                )

        stack = stack[: len(stack) - arg_count]

        for return_type in signature.return_types:
            stack.append(
                self._update_return_type(deepcopy(return_type), placeholder_types)
            )

        return stack

    def _match_signature_items(
        self,
        expected_type: VariableType,
        type: VariableType,
        placeholder_types: Dict[str, VariableType],
    ) -> bool:
        if expected_type.root_type == RootType.PLACEHOLDER:
            if expected_type.name in placeholder_types:
                return placeholder_types[expected_type.name] == type

            placeholder_types[expected_type.name] = type
            return True

        else:
            if expected_type.root_type == RootType.PLACEHOLDER:
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

    def _update_return_type(
        self, return_type: VariableType, placeholder_types: Dict[str, VariableType]
    ) -> VariableType:
        if return_type.root_type == RootType.PLACEHOLDER:
            if return_type.name not in placeholder_types:
                raise NotImplementedError

            return placeholder_types[return_type.name]

        elif isinstance(return_type, VariableType):
            for i, param in enumerate(return_type.type_params):
                return_type.type_params[i] = self._update_return_type(
                    param, placeholder_types
                )

            return return_type

        else:  # pragma: nocover
            assert False

    def _check_integer_literal(
        self, node: AaaTreeNode, type_stack: List[VariableType]
    ) -> List[VariableType]:
        assert isinstance(node, IntegerLiteral)
        return type_stack + [Int]

    def _check_string_literal(
        self, node: AaaTreeNode, type_stack: List[VariableType]
    ) -> List[VariableType]:
        assert isinstance(node, StringLiteral)
        return type_stack + [Str]

    def _check_boolean_literal(
        self, node: AaaTreeNode, type_stack: List[VariableType]
    ) -> List[VariableType]:
        assert isinstance(node, BooleanLiteral)
        return type_stack + [Bool]

    def _check_operator(
        self, node: AaaTreeNode, type_stack: List[VariableType]
    ) -> List[VariableType]:
        assert isinstance(node, Operator)

        signatures = self.program._builtins.functions[node.value]

        stack: Optional[List[VariableType]] = None
        last_stack_type_error: Optional[StackTypesError] = None

        for _, signature in signatures:
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

    def _check_parsed_type(
        self, node: AaaTreeNode, type_stack: List[VariableType]
    ) -> List[VariableType]:
        assert isinstance(node, ParsedType)

        type = VariableType.from_parsed_type(node)
        return type_stack + [type]

    def _check_condition(
        self, node: AaaTreeNode, type_stack: List[VariableType]
    ) -> None:
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
                type_stack=type_stack,
                condition_stack=condition_stack,
            )

    def _check_branch(
        self, node: AaaTreeNode, type_stack: List[VariableType]
    ) -> List[VariableType]:
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
                type_stack=type_stack,
                if_stack=if_stack,
                else_stack=else_stack,
            )

        # we can return either one, since they are the same
        return if_stack

    def _check_loop(
        self, node: AaaTreeNode, type_stack: List[VariableType]
    ) -> List[VariableType]:
        assert isinstance(node, Loop)

        self._check_condition(node.condition, copy(type_stack))

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for the loop body.
        loop_stack = self._check_function_body(node.body, copy(type_stack))

        if loop_stack != type_stack:
            raise LoopTypeError(
                file=self.file,
                function=self.function,
                type_stack=type_stack,
                loop_stack=loop_stack,
            )

        # we can return either one, since they are the same
        return loop_stack

    def _check_identifier(
        self, node: AaaTreeNode, type_stack: List[VariableType]
    ) -> List[VariableType]:
        assert isinstance(node, Identifier)
        # If it's a function argument, just push the type.

        arg_type = self._get_func_arg_type(node.name)

        if arg_type is not None:
            return copy(type_stack) + [arg_type]

        # If it's not a function argument, we must be calling a function.
        identifier = self.program.get_identifier(self.file, node.name)

        if not identifier:
            raise UnknownIdentifier(
                file=self.file, function=self.function, identifier=node
            )

        if isinstance(identifier, Function):
            signature = self._get_function_signature(identifier)
            return self._check_and_apply_signature(
                copy(type_stack), signature, identifier
            )

        elif isinstance(identifier, Struct):
            return copy(type_stack) + [
                VariableType(
                    root_type=RootType.STRUCT,
                    type_params=[],
                    name=identifier.name,
                )
            ]

        elif isinstance(identifier, BuiltinFunction):
            signature = self.program._builtins.functions[identifier.name][0][1]
            return self._check_and_apply_signature(
                copy(type_stack), signature, identifier
            )

        else:  # pragma: nocover
            assert False

    def _check_function_body(
        self, node: AaaTreeNode, type_stack: List[VariableType]
    ) -> List[VariableType]:
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
            elif isinstance(child_node, MemberFunctionName):
                stack = self._check_member_function_call(child_node, copy(stack))
            elif isinstance(child_node, Operator):
                stack = self._check_operator(child_node, copy(stack))
            elif isinstance(child_node, StringLiteral):
                stack = self._check_string_literal(child_node, copy(stack))
            elif isinstance(child_node, ParsedType):
                stack = self._check_parsed_type(child_node, copy(stack))
            elif isinstance(child_node, StructFieldQuery):
                stack = self._check_type_struct_field_query(child_node, copy(stack))
            elif isinstance(child_node, StructFieldUpdate):
                stack = self._check_type_struct_field_update(child_node, copy(stack))
            else:  # pragma nocover
                assert False

        return stack

    def _check_member_function_call(
        self, node: AaaTreeNode, type_stack: List[VariableType]
    ) -> List[VariableType]:
        assert isinstance(node, MemberFunctionName)

        key = f"{node.type_name}:{node.func_name}"

        signatures = self.program._builtins.functions.get(key)

        if signatures is not None:
            # All builtin member functions should be listed in the builtins file
            # so this should not raise a KeyError.
            builtin_tuples = self.program._builtins.functions[key]

            # All builtin member functions should have a unique signature
            assert len(builtin_tuples) == 1

            builtin_tuple = builtin_tuples[0]
            _, signature = builtin_tuple

        else:
            file_identifiers = self.program.identifiers[self.file]

            try:
                function = file_identifiers[key]
            except KeyError as e:
                raise NotImplementedError from e

            assert isinstance(function, Function)
            signature = self._get_function_signature(function)

        return self._check_and_apply_signature(type_stack, signature, node)

    def _check_function(
        self, node: AaaTreeNode, type_stack: List[VariableType]
    ) -> List[VariableType]:
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
                )

        if isinstance(node.name, MemberFunctionName):

            signature = self._get_function_signature(node)
            struct = self.program.identifiers[self.file][node.name.type_name]
            assert isinstance(struct, Struct)

            if TYPE_CHECKING:  # pragma: nocover
                assert isinstance(signature.arg_types[0], VariableType)
                assert isinstance(signature.return_types[0], VariableType)

            # A memberfunction on a type foo needs to have foo as
            # type of thefirst argument and first return type
            if (
                len(signature.arg_types) == 0
                or signature.arg_types[0].root_type != RootType.STRUCT
                or signature.arg_types[0].name != struct.name
                or len(signature.return_types) == 0
                or signature.return_types[0].root_type != RootType.STRUCT
                or signature.return_types[0].name != struct.name
            ):
                raise InvalidMemberFunctionSignature(
                    file=self.file,
                    function=node,
                    struct=struct,
                    signature=signature,
                )

        for arg_offset, arg in enumerate(node.arguments):
            colliding_identifier = self.program.get_identifier(self.file, arg.name)

            if colliding_identifier:
                raise CollidingIdentifier(
                    file=self.file,
                    colliding=arg,
                    found=colliding_identifier,
                )

            if arg.name == node.name:
                raise CollidingIdentifier(file=self.file, colliding=arg, found=node)

            for preceding_arg in node.arguments[:arg_offset]:
                if arg.name == preceding_arg.name:
                    raise CollidingIdentifier(
                        file=self.file,
                        colliding=arg,
                        found=preceding_arg,
                    )

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
                function=self.function,
                struct=struct,
                field_name=field_name,
            )

        return VariableType.from_parsed_type(field_type)

    def _check_type_struct_field_query(
        self, node: AaaTreeNode, type_stack: List[VariableType]
    ) -> List[VariableType]:
        assert isinstance(node, StructFieldQuery)

        type_stack = self._check_string_literal(node.field_name, copy(type_stack))

        if len(type_stack) < 2:
            raise StackTypesError(
                file=self.file,
                function=self.function,
                signature=StructQuerySignature(),
                type_stack=type_stack,
                func_like=node,
            )

        struct_type, field_selector_type = type_stack[-2:]

        assert isinstance(struct_type, VariableType)
        assert isinstance(field_selector_type, VariableType)

        # This is enforced by the parser
        assert field_selector_type.root_type == RootType.STRING

        if struct_type.root_type != RootType.STRUCT:
            raise GetFieldOfNonStructTypeError(
                file=self.file,
                type_stack=type_stack,
                function=self.function,
                field_query=node,
            )

        struct_name = struct_type.name

        # These should not raise, they are enforced by the Program class
        struct = self.program.identifiers[self.file][struct_name]
        assert isinstance(struct, Struct)

        field_type = self._get_struct_field_type(node, struct)

        type_stack.pop()
        type_stack.append(field_type)
        return type_stack

    def _check_type_struct_field_update(
        self, node: AaaTreeNode, type_stack: List[VariableType]
    ) -> List[VariableType]:
        assert isinstance(node, StructFieldUpdate)
        type_stack = self._check_string_literal(node.field_name, copy(type_stack))

        type_stack_before = type_stack
        type_stack = self._check_function_body(
            node.new_value_expr, copy(type_stack_before)
        )

        if len(type_stack) < 3:
            raise StackTypesError(
                file=self.file,
                function=self.function,
                signature=StructUpdateSignature(),
                type_stack=type_stack,
                func_like=node,
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
            raise StructUpdateStackError(
                file=self.file,
                function=self.function,
                type_stack=type_stack,
                type_stack_before=type_stack_before,
                field_update=node,
            )

        struct_name = struct_type.name

        if struct_type.root_type != RootType.STRUCT:
            raise SetFieldOfNonStructTypeError(
                file=self.file,
                type_stack=type_stack,
                function=self.function,
                field_update=node,
            )

        # These should not raise, they are enforced by the Program class
        struct = self.program.identifiers[self.file][struct_name]
        assert isinstance(struct, Struct)

        field_type = self._get_struct_field_type(node, struct)

        if field_type != update_expr_type:
            raise StructUpdateTypeError(
                file=self.file,
                function=self.function,
                type_stack=type_stack,
                struct=struct,
                field_name=node.field_name.value,
                found_type=update_expr_type,
                expected_type=field_selector_type,
                field_update=node,
            )

        # drop field_selector and update value
        return type_stack[:-2]

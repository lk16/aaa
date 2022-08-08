from copy import copy, deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Union

from lang.models.parse import (
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
from lang.models.typing import (
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
        self, type_stack: List[VariableType]
    ) -> List[VariableType]:
        return type_stack + [Int]

    def _check_string_literal(
        self, type_stack: List[VariableType]
    ) -> List[VariableType]:
        return type_stack + [Str]

    def _check_boolean_literal(
        self, type_stack: List[VariableType]
    ) -> List[VariableType]:
        return type_stack + [Bool]

    def _check_operator(
        self, operator: Operator, type_stack: List[VariableType]
    ) -> List[VariableType]:
        builtin_function = self.program._builtins.functions[operator.value]
        signature = Signature.from_builtin_function(builtin_function)
        return self._check_and_apply_signature(copy(type_stack), signature, operator)

    def _check_parsed_type(
        self, parsed_type: ParsedType, type_stack: List[VariableType]
    ) -> List[VariableType]:
        type = VariableType.from_parsed_type(parsed_type)
        return type_stack + [type]

    def _check_condition(
        self, function_body: FunctionBody, type_stack: List[VariableType]
    ) -> None:
        # Condition is a special type of function body:
        # It should push exactly one boolean and not modify the type stack under it
        condition_stack = self._check_function_body(function_body, copy(type_stack))

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
        self, branch: Branch, type_stack: List[VariableType]
    ) -> List[VariableType]:
        self._check_condition(branch.condition, copy(type_stack))

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for both the if- and else- bodies.
        if_stack = self._check_function_body(branch.if_body, copy(type_stack))
        else_stack = self._check_function_body(branch.else_body, copy(type_stack))

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
        self, loop: Loop, type_stack: List[VariableType]
    ) -> List[VariableType]:
        self._check_condition(loop.condition, copy(type_stack))

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for the loop body.
        loop_stack = self._check_function_body(loop.body, copy(type_stack))

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
        self, identifier: Identifier, type_stack: List[VariableType]
    ) -> List[VariableType]:
        arg_type = self._get_func_arg_type(identifier.name)

        if arg_type is not None:
            # If it's a function argument, just push the type.
            return copy(type_stack) + [arg_type]

        # If it's not a function argument, we must be calling a function.

        try:
            builtin_function = self.program._builtins.functions[identifier.name]
        except KeyError:
            pass
        else:
            signature = Signature.from_builtin_function(builtin_function)
            return self._check_and_apply_signature(
                copy(type_stack), signature, builtin_function
            )

        identified = self.program.get_identifier(self.file, identifier.name)

        if not identified:
            raise UnknownIdentifier(
                file=self.file, function=self.function, identifier=identifier
            )

        if isinstance(identified, Function):
            signature = self._get_function_signature(identified)
            return self._check_and_apply_signature(
                copy(type_stack), signature, identified
            )

        elif isinstance(identified, Struct):
            return copy(type_stack) + [
                VariableType(
                    root_type=RootType.STRUCT,
                    type_params=[],
                    name=identified.name,
                )
            ]

        elif isinstance(identified, BuiltinFunction):
            builtin_function = self.program._builtins.functions[identifier.name]
            signature = Signature.from_builtin_function(builtin_function)
            return self._check_and_apply_signature(
                copy(type_stack), signature, identified
            )

        else:  # pragma: nocover
            assert False

    def _check_function_body(
        self, function_body: FunctionBody, type_stack: List[VariableType]
    ) -> List[VariableType]:

        stack = copy(type_stack)
        for child_node in function_body.items:
            if isinstance(child_node, BooleanLiteral):
                stack = self._check_boolean_literal(copy(stack))
            elif isinstance(child_node, Branch):
                stack = self._check_branch(child_node, copy(stack))
            elif isinstance(child_node, Identifier):
                stack = self._check_identifier(child_node, copy(stack))
            elif isinstance(child_node, IntegerLiteral):
                stack = self._check_integer_literal(copy(stack))
            elif isinstance(child_node, Loop):
                stack = self._check_loop(child_node, copy(stack))
            elif isinstance(child_node, MemberFunctionName):
                stack = self._check_member_function_call(child_node, copy(stack))
            elif isinstance(child_node, Operator):
                stack = self._check_operator(child_node, copy(stack))
            elif isinstance(child_node, StringLiteral):
                stack = self._check_string_literal(copy(stack))
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
        self, member_function_name: MemberFunctionName, type_stack: List[VariableType]
    ) -> List[VariableType]:
        key = f"{member_function_name.type_name}:{member_function_name.func_name}"

        builtin_function = self.program._builtins.functions.get(key)

        if builtin_function:
            # All builtin member functions should be listed in the builtins file
            # so this should not raise a KeyError.
            signature = Signature.from_builtin_function(builtin_function)
        else:
            file_identifiers = self.program.identifiers[self.file]

            try:
                function = file_identifiers[key]
            except KeyError as e:
                raise NotImplementedError from e

            assert isinstance(function, Function)
            signature = self._get_function_signature(function)

        return self._check_and_apply_signature(
            type_stack, signature, member_function_name
        )

    def _check_function(
        self, function: Function, type_stack: List[VariableType]
    ) -> List[VariableType]:
        if function.name == "main":
            if not all(
                [
                    len(function.arguments) == 0,
                    len(function.return_types) == 0,
                ]
            ):
                raise InvalidMainSignuture(
                    file=self.file,
                    function=self.function,
                )

        if isinstance(function.name, MemberFunctionName):

            signature = self._get_function_signature(function)
            struct = self.program.identifiers[self.file][function.name.type_name]
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
                    function=function,
                    struct=struct,
                    signature=signature,
                )

        for arg_offset, arg in enumerate(function.arguments):
            colliding_identifier = self.program.get_identifier(self.file, arg.name)

            if colliding_identifier:
                raise CollidingIdentifier(
                    file=self.file,
                    colliding=arg,
                    found=colliding_identifier,
                )

            if arg.name == function.name:
                raise CollidingIdentifier(file=self.file, colliding=arg, found=function)

            for preceding_arg in function.arguments[:arg_offset]:
                if arg.name == preceding_arg.name:
                    raise CollidingIdentifier(
                        file=self.file,
                        colliding=arg,
                        found=preceding_arg,
                    )

        return self._check_function_body(function.body, type_stack)

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
        self, field_query: StructFieldQuery, type_stack: List[VariableType]
    ) -> List[VariableType]:
        type_stack = self._check_string_literal(copy(type_stack))

        if len(type_stack) < 2:
            raise StackTypesError(
                file=self.file,
                function=self.function,
                signature=StructQuerySignature(),
                type_stack=type_stack,
                func_like=field_query,
            )

        struct_type, field_selector_type = type_stack[-2:]

        # This is enforced by the parser
        assert field_selector_type.root_type == RootType.STRING

        if struct_type.root_type != RootType.STRUCT:
            raise GetFieldOfNonStructTypeError(
                file=self.file,
                type_stack=type_stack,
                function=self.function,
                field_query=field_query,
            )

        struct_name = struct_type.name

        # These should not raise, they are enforced by the Program class
        struct = self.program.identifiers[self.file][struct_name]
        assert isinstance(struct, Struct)

        field_type = self._get_struct_field_type(field_query, struct)

        type_stack.pop()
        type_stack.append(field_type)
        return type_stack

    def _check_type_struct_field_update(
        self, field_update: StructFieldUpdate, type_stack: List[VariableType]
    ) -> List[VariableType]:
        type_stack = self._check_string_literal(copy(type_stack))

        type_stack_before = type_stack
        type_stack = self._check_function_body(
            field_update.new_value_expr, copy(type_stack_before)
        )

        if len(type_stack) < 3:
            raise StackTypesError(
                file=self.file,
                function=self.function,
                signature=StructUpdateSignature(),
                type_stack=type_stack,
                func_like=field_update,
            )

        struct_type, field_selector_type, update_expr_type = type_stack[-3:]

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
                field_update=field_update,
            )

        struct_name = struct_type.name

        if struct_type.root_type != RootType.STRUCT:
            raise SetFieldOfNonStructTypeError(
                file=self.file,
                type_stack=type_stack,
                function=self.function,
                field_update=field_update,
            )

        # These should not raise, they are enforced by the Program class
        struct = self.program.identifiers[self.file][struct_name]
        assert isinstance(struct, Struct)

        field_type = self._get_struct_field_type(field_update, struct)

        if field_type != update_expr_type:
            raise StructUpdateTypeError(
                file=self.file,
                function=self.function,
                type_stack=type_stack,
                struct=struct,
                field_name=field_update.field_name.value,
                found_type=update_expr_type,
                expected_type=field_selector_type,
                field_update=field_update,
            )

        # drop field_selector and update value
        return type_stack[:-2]

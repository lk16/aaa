from copy import copy
from pathlib import Path
from typing import Dict, List, Tuple

from lark.lexer import Token

from aaa.cross_referencer.models import (
    BooleanLiteral,
    Branch,
    CrossReferencerOutput,
    Function,
    FunctionBody,
    Identifier,
    IdentifierCallingFunction,
    IdentifierCallingType,
    IdentifierUsingArgument,
    IntegerLiteral,
    Loop,
    StringLiteral,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
    Unresolved,
    VariableType,
)
from aaa.parser import models as parser
from aaa.type_checker.exceptions import (
    BranchTypeError,
    ConditionTypeError,
    FunctionTypeError,
    InvalidMainSignuture,
    InvalidMemberFunctionSignature,
    LoopTypeError,
    StackTypesError,
    StructUpdateStackError,
    StructUpdateTypeError,
    TypeCheckerException,
    UnknownStructField,
)
from aaa.type_checker.models import (
    Signature,
    StructQuerySignature,
    StructUpdateSignature,
    TypeCheckerOutput,
)


class TypeChecker:
    def __init__(self, cross_referencer_output: CrossReferencerOutput) -> None:
        self.functions = cross_referencer_output.functions
        self.types = cross_referencer_output.types
        self.imports = cross_referencer_output.imports
        self.builtins_path = cross_referencer_output.builtins_path
        self.signatures: Dict[Tuple[Path, str], Signature] = {}
        self.exceptions: List[TypeCheckerException] = []

    def run(self) -> TypeCheckerOutput:
        for function in self.functions.values():
            assert not isinstance(function.arguments, Unresolved)
            assert not isinstance(function.return_types, Unresolved)

            self.signatures[function.identify()] = Signature(
                arguments=[arg.type for arg in function.arguments],
                return_types=function.return_types,
            )

        for function in self.functions.values():
            try:
                self._check(function)
            except TypeCheckerException as e:
                self.exceptions.append(e)

        return TypeCheckerOutput(exceptions=self.exceptions)

    def _check(self, function: Function) -> None:
        if function.file == self.builtins_path:
            # builtins can't be type checked
            return

        expected_return_types = self.signatures[function.identify()].return_types
        computed_return_types = self._check_function(function, [])

        if computed_return_types != expected_return_types:
            raise FunctionTypeError(
                file=function.file,
                token=function.token,
                function=function,
                expected_return_types=expected_return_types,
                computed_return_types=computed_return_types,
            )

    def _check_function_call(
        self,
        function: Function,
        type_stack: List[VariableType],
        called_function: Function,
        called_function_token: Token,
    ) -> List[VariableType]:

        signature = self.signatures[called_function.identify()]

        stack = copy(type_stack)
        arg_count = len(signature.arguments)

        if len(stack) < arg_count:
            raise StackTypesError(
                file=function.file,
                token=called_function_token,
                function=function,
                signature=signature,
                type_stack=type_stack,
                func_like=called_function,
            )

        placeholder_types: Dict[str, VariableType] = {}
        expected_types = signature.arguments
        types = stack[len(stack) - arg_count :]

        for expected_type, type in zip(expected_types, types, strict=True):
            match_result = self._match_signature_items(
                function, expected_type, type, placeholder_types
            )

            if not match_result:

                raise StackTypesError(
                    file=function.file,
                    token=called_function_token,
                    function=function,
                    signature=signature,
                    type_stack=type_stack,
                    func_like=called_function,
                )

        stack = stack[: len(stack) - arg_count]

        for return_type in signature.return_types:
            stack.append(
                self._update_return_type(function, return_type, placeholder_types)
            )

        return stack

    def _match_signature_items(
        self,
        function: Function,
        expected_type: VariableType,
        type: VariableType,
        placeholder_types: Dict[str, VariableType],
    ) -> bool:
        if expected_type.is_placeholder:
            if expected_type.name in placeholder_types:
                return placeholder_types[expected_type.name] == type

            placeholder_types[expected_type.name] = type
            return True

        else:
            if expected_type.type is not type.type:
                return False

            if len(type.params) != len(expected_type.params):
                return False

            for expected_param, param in zip(expected_type.params, type.params):
                match_result = self._match_signature_items(
                    function,
                    expected_param,
                    param,
                    placeholder_types,
                )

                if not match_result:
                    return False

            return True

    def _update_return_type(
        self,
        function: Function,
        return_type: VariableType,
        placeholder_types: Dict[str, VariableType],
    ) -> VariableType:
        if return_type.is_placeholder:
            if return_type.name not in placeholder_types:
                raise NotImplementedError

            return placeholder_types[return_type.name]

        for i, param in enumerate(return_type.params):
            return_type.params[i] = self._update_return_type(
                function, param, placeholder_types
            )

        return return_type

    def _get_builtin_var_type(self, type_name: str) -> VariableType:
        type = self.types[(self.builtins_path, type_name)]

        # TODO get rid of dummy_token and dummy_type_literal

        dummy_token = Token(type_="", value="")  # type: ignore

        dummy_type_literal = parser.TypeLiteral(
            identifier=parser.Identifier(
                name=type_name, token=dummy_token, file=self.builtins_path
            ),
            params=parser.TypeParameters(
                value=[], token=dummy_token, file=self.builtins_path
            ),
            token=dummy_token,
            file=Path(self.builtins_path),
        )

        return VariableType(
            parsed=dummy_type_literal,
            type=type,
            params=[],
            is_placeholder=False,
        )

    def _get_bool_var_type(self) -> VariableType:
        return self._get_builtin_var_type("bool")

    def _get_str_var_type(self) -> VariableType:
        return self._get_builtin_var_type("str")

    def _get_int_var_type(self) -> VariableType:
        return self._get_builtin_var_type("int")

    def _check_integer_literal(
        self, type_stack: List[VariableType]
    ) -> List[VariableType]:
        return type_stack + [self._get_int_var_type()]

    def _check_string_literal(
        self, type_stack: List[VariableType]
    ) -> List[VariableType]:
        return type_stack + [self._get_str_var_type()]

    def _check_boolean_literal(
        self, type_stack: List[VariableType]
    ) -> List[VariableType]:
        return type_stack + [self._get_bool_var_type()]

    def _check_parsed_type(
        self, var_type: VariableType, type_stack: List[VariableType]
    ) -> List[VariableType]:
        return type_stack + [var_type]

    def _check_condition(
        self,
        function: Function,
        function_body: FunctionBody,
        type_stack: List[VariableType],
    ) -> None:
        # Condition is a special type of function body:
        # It should push exactly one boolean and not modify the type stack under it
        condition_stack = self._check_function_body(
            function, function_body, copy(type_stack)
        )

        if condition_stack != type_stack + [self._get_bool_var_type()]:
            raise ConditionTypeError(
                file=function.file,
                token=function_body.token,
                function=function,
                type_stack=type_stack,
                condition_stack=condition_stack,
            )

    def _check_branch(
        self,
        function: Function,
        branch: Branch,
        type_stack: List[VariableType],
    ) -> List[VariableType]:
        self._check_condition(function, branch.condition, copy(type_stack))

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for both the if- and else- bodies.
        if_stack = self._check_function_body(function, branch.if_body, copy(type_stack))
        else_stack = self._check_function_body(
            function, branch.else_body, copy(type_stack)
        )

        # Regardless whether the if- or else- branch is taken,
        # afterwards the stack should be the same.
        if if_stack != else_stack:
            raise BranchTypeError(
                file=function.file,
                token=branch.token,
                function=function,
                type_stack=type_stack,
                if_stack=if_stack,
                else_stack=else_stack,
            )

        # we can return either one, since they are the same
        return if_stack

    def _check_loop(
        self, function: Function, loop: Loop, type_stack: List[VariableType]
    ) -> List[VariableType]:
        self._check_condition(function, loop.condition, copy(type_stack))

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for the loop body.
        loop_stack = self._check_function_body(function, loop.body, copy(type_stack))

        if loop_stack != type_stack:
            raise LoopTypeError(
                file=function.file,
                token=loop.token,
                function=function,
                type_stack=type_stack,
                loop_stack=loop_stack,
            )

        # we can return either one, since they are the same
        return loop_stack

    def _check_function_body(
        self,
        function: Function,
        function_body: FunctionBody,
        type_stack: List[VariableType],
    ) -> List[VariableType]:

        stack = copy(type_stack)
        for child_node in function_body.items:
            if isinstance(child_node, BooleanLiteral):
                stack = self._check_boolean_literal(copy(stack))
            elif isinstance(child_node, Branch):
                stack = self._check_branch(function, child_node, copy(stack))
            elif isinstance(child_node, IntegerLiteral):
                stack = self._check_integer_literal(copy(stack))
            elif isinstance(child_node, Loop):
                stack = self._check_loop(function, child_node, copy(stack))
            elif isinstance(child_node, StringLiteral):
                stack = self._check_string_literal(copy(stack))
            elif isinstance(child_node, VariableType):
                stack = self._check_parsed_type(child_node, copy(stack))
            elif isinstance(child_node, StructFieldQuery):
                stack = self._check_type_struct_field_query(
                    function, child_node, copy(stack)
                )
            elif isinstance(child_node, StructFieldUpdate):
                stack = self._check_type_struct_field_update(
                    function, child_node, copy(stack)
                )
            elif isinstance(child_node, Identifier):
                stack = self._check_identifier(function, child_node, copy(stack))
            else:  # pragma nocover
                assert False

        return stack

    def _check_identifier(
        self,
        function: Function,
        identifier: Identifier,
        type_stack: List[VariableType],
    ) -> List[VariableType]:
        if isinstance(identifier.kind, IdentifierUsingArgument):
            # Push argument on stack
            return type_stack + [identifier.kind.arg_type]

        elif isinstance(identifier.kind, IdentifierCallingFunction):
            # Function was called, apply signature of called function
            called_function = identifier.kind.function
            return self._check_function_call(
                function, type_stack, called_function, identifier.token
            )
        elif isinstance(identifier.kind, IdentifierCallingType):
            # TODO should identifier.kind.type be VariableType instead of Type?
            raise NotImplementedError
        else:  # pragma: nocover
            assert False

    def _check_function(
        self, function: Function, type_stack: List[VariableType]
    ) -> List[VariableType]:
        assert not isinstance(function.arguments, Unresolved)
        assert not isinstance(function.return_types, Unresolved)

        if function.name == "main":
            if not all(
                [
                    len(function.arguments) == 0,
                    len(function.return_types) == 0,
                ]
            ):
                raise InvalidMainSignuture(
                    file=function.file,
                    token=function.token,
                    function=function,
                )

        if function.is_member_function():
            signature = self.signatures[function.identify()]
            struct_type = self.types[(function.file, function.struct_name)]

            # A memberfunction on a type foo needs to have foo as
            # type of thefirst argument and first return type
            if (
                len(signature.arguments) == 0
                or signature.arguments[0].type != struct_type
                or len(signature.return_types) == 0
                or signature.return_types[0].type != struct_type
            ):
                raise InvalidMemberFunctionSignature(
                    file=function.file,
                    token=function.token,
                    function=function,
                    struct_type=struct_type,
                    signature=signature,
                )

        assert not isinstance(function.body, Unresolved)
        return self._check_function_body(function, function.body, type_stack)

    def _get_struct_field_type(
        self,
        function: Function,
        node: StructFieldQuery | StructFieldUpdate,
        struct_type: Type,
    ) -> VariableType:
        field_name = node.field_name.value

        assert not isinstance(struct_type.fields, Unresolved)

        try:
            field_type = struct_type.fields[field_name]
        except KeyError as e:
            raise UnknownStructField(
                file=function.file,
                token=node.token,
                function=function,
                struct_type=struct_type,
                field_name=field_name,
            ) from e

        assert not isinstance(field_type, Unresolved)
        return field_type

    def _check_type_struct_field_query(
        self,
        function: Function,
        field_query: StructFieldQuery,
        type_stack: List[VariableType],
    ) -> List[VariableType]:
        type_stack = self._check_string_literal(copy(type_stack))

        if len(type_stack) < 2:
            raise StackTypesError(
                file=function.file,
                token=field_query.token,
                function=function,
                signature=StructQuerySignature(),
                type_stack=type_stack,
                func_like=field_query,
            )

        struct_var_type, field_selector_type = type_stack[-2:]

        # This is enforced by the parser
        assert field_selector_type == self._get_str_var_type()

        field_type = self._get_struct_field_type(
            function, field_query, struct_var_type.type
        )

        type_stack.pop()
        type_stack.append(field_type)
        return type_stack

    def _check_type_struct_field_update(
        self,
        function: Function,
        field_update: StructFieldUpdate,
        type_stack: List[VariableType],
    ) -> List[VariableType]:
        type_stack = self._check_string_literal(copy(type_stack))

        type_stack_before = type_stack
        type_stack = self._check_function_body(
            function, field_update.new_value_expr, copy(type_stack_before)
        )

        if len(type_stack) < 3:
            raise StackTypesError(
                file=function.file,
                token=field_update.token,
                function=function,
                signature=StructUpdateSignature(),
                type_stack=type_stack,
                func_like=field_update,
            )

        struct_var_type, field_selector_type, update_expr_type = type_stack[-3:]
        struct_type = struct_var_type.type

        if not all(
            [
                len(type_stack_before) == len(type_stack) - 1,
                type_stack_before == type_stack[:-1],
            ]
        ):
            raise StructUpdateStackError(
                file=function.file,
                token=field_update.token,
                function=function,
                type_stack=type_stack,
                type_stack_before=type_stack_before,
            )

        field_type = self._get_struct_field_type(function, field_update, struct_type)

        if field_type != update_expr_type:
            raise StructUpdateTypeError(
                file=function.file,
                token=field_update.new_value_expr.token,
                function=function,
                type_stack=type_stack,
                struct_type=struct_type,
                field_name=field_update.field_name.value,
                found_type=update_expr_type,
                expected_type=field_selector_type,
            )

        # drop field_selector and update value
        return type_stack[:-2]

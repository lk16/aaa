from copy import copy
from pathlib import Path
from typing import Dict, List, Tuple

from aaa import AaaRunnerException
from aaa.cross_referencer.models import (
    BooleanLiteral,
    Branch,
    CallArgument,
    CallFunction,
    CallType,
    CrossReferencerOutput,
    Function,
    FunctionBody,
    IntegerLiteral,
    Loop,
    StringLiteral,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
    VariableType,
)
from aaa.type_checker.exceptions import (
    BranchTypeError,
    ConditionTypeError,
    FunctionTypeError,
    InvalidMainSignuture,
    InvalidMemberFunctionSignature,
    InvalidTestSignuture,
    LoopTypeError,
    MainFunctionNotFound,
    StackTypesError,
    StructUpdateStackError,
    StructUpdateTypeError,
    TypeCheckerException,
    UnknownField,
)
from aaa.type_checker.models import (
    Signature,
    StructQuerySignature,
    StructUpdateSignature,
)


class TypeChecker:
    def __init__(
        self, cross_referencer_output: CrossReferencerOutput, verbose: bool
    ) -> None:
        self.functions = cross_referencer_output.functions
        self.types = cross_referencer_output.types
        self.imports = cross_referencer_output.imports
        self.builtins_path = cross_referencer_output.builtins_path
        self.entrypoint = cross_referencer_output.entrypoint
        self.signatures: Dict[Tuple[Path, str], Signature] = {}
        self.exceptions: List[TypeCheckerException] = []
        self.verbose = verbose  # TODO use

    def run(self) -> None:
        for function in self.functions.values():
            self.signatures[function.identify()] = Signature(
                arguments=[arg.var_type for arg in function.arguments],
                return_types=function.return_types,
            )

        for function in self.functions.values():
            try:
                self._check(function)
            except TypeCheckerException as e:
                self.exceptions.append(e)

        self._check_main_function()

        if self.exceptions:
            raise AaaRunnerException(self.exceptions)

    def _check(self, function: Function) -> None:
        if function.position.file == self.builtins_path:
            # builtins can't be type checked
            return

        expected_return_types = self.signatures[function.identify()].return_types
        computed_return_types = self._check_function(function, [])

        if computed_return_types != expected_return_types:
            raise FunctionTypeError(
                function.position,
                function,
                expected_return_types,
                computed_return_types,
            )

    def _check_main_function(self) -> None:
        try:
            self.functions[(self.entrypoint, "main")]
        except KeyError:
            e = MainFunctionNotFound(self.entrypoint)
            self.exceptions.append(e)

    def _match_signature_items(
        self,
        function: Function,
        expected_var_type: VariableType,
        var_type: VariableType,
        placeholder_types: Dict[str, VariableType],
    ) -> bool:
        if expected_var_type.is_placeholder:
            if expected_var_type.name in placeholder_types:
                return placeholder_types[expected_var_type.name] == var_type

            placeholder_types[expected_var_type.name] = var_type
            return True

        else:
            if expected_var_type.type is not var_type.type:
                return False

            if len(var_type.params) != len(expected_var_type.params):
                return False

            for expected_param, param in zip(expected_var_type.params, var_type.params):
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
                # TODO
                raise NotImplementedError

            return placeholder_types[return_type.name]

        for i, param in enumerate(return_type.params):
            return_type.params[i] = self._update_return_type(
                function, param, placeholder_types
            )

        return return_type

    def _get_builtin_var_type(self, type_name: str) -> VariableType:
        type = self.types[(self.builtins_path, type_name)]
        return VariableType(type, [], False, type.position)

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
                position=function_body.position,
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

        if branch.else_body:
            else_stack = self._check_function_body(
                function, branch.else_body, copy(type_stack)
            )
        else:
            else_stack = copy(type_stack)

        # Regardless whether the if- or else- branch is taken,
        # afterwards the stack should be the same.
        if if_stack != else_stack:
            raise BranchTypeError(
                position=branch.position,
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
                position=loop.position,
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
            elif isinstance(child_node, StructFieldQuery):
                stack = self._check_type_struct_field_query(
                    function, child_node, copy(stack)
                )
            elif isinstance(child_node, StructFieldUpdate):
                stack = self._check_type_struct_field_update(
                    function, child_node, copy(stack)
                )
            elif isinstance(child_node, CallArgument):
                stack = self._check_call_argument(function, child_node, copy(stack))
            elif isinstance(child_node, CallFunction):
                stack = self._check_call_function(function, child_node, copy(stack))
            elif isinstance(child_node, CallType):
                stack = self._check_call_type(function, child_node, copy(stack))
            else:  # pragma nocover
                assert False

        return stack

    def _check_call_argument(
        self,
        function: Function,
        call_arg: CallArgument,
        type_stack: List[VariableType],
    ) -> List[VariableType]:
        # Push argument on stack
        arg_var_type = call_arg.argument.var_type
        return type_stack + [arg_var_type]

    def _check_call_function(
        self,
        function: Function,
        call_function: CallFunction,
        type_stack: List[VariableType],
    ) -> List[VariableType]:
        signature = self.signatures[call_function.function.identify()]

        stack = copy(type_stack)
        arg_count = len(signature.arguments)

        if len(stack) < arg_count:
            raise StackTypesError(
                function=function,
                signature=signature,
                type_stack=type_stack,
                func_like=call_function.function,
                position=call_function.position,
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
                    function=function,
                    signature=signature,
                    type_stack=type_stack,
                    func_like=call_function.function,
                    position=call_function.position,
                )

        stack = stack[: len(stack) - arg_count]

        for return_type in signature.return_types:
            stack.append(
                self._update_return_type(function, return_type, placeholder_types)
            )

        return stack

    def _check_call_type(
        self,
        function: Function,
        call_type: CallType,
        type_stack: List[VariableType],
    ) -> List[VariableType]:
        return type_stack + [call_type.var_type]

    def _check_function(
        self, function: Function, type_stack: List[VariableType]
    ) -> List[VariableType]:
        if function.name == "main":
            if not all(
                [
                    len(function.arguments) == 0,
                    len(function.return_types) == 0,
                    len(function.type_params) == 0,
                ]
            ):
                raise InvalidMainSignuture(function.position, function)

        if (
            function.struct_name == ""
            and function.func_name.startswith("test_")
            and function.position.file.name.startswith("test_")
        ):
            if not all(
                [
                    len(function.arguments) == 0,
                    len(function.return_types) == 0,
                    len(function.type_params) == 0,
                ]
            ):
                raise InvalidTestSignuture(function.position, function)

        if function.is_member_function():
            signature = self.signatures[function.identify()]
            struct_type = self.types[(function.position.file, function.struct_name)]

            # A memberfunction on a type foo needs to take a foo object as the first argument
            if (
                len(signature.arguments) == 0
                or signature.arguments[0].type != struct_type
            ):
                raise InvalidMemberFunctionSignature(
                    function.position, function, struct_type, signature
                )

        assert function.body
        return self._check_function_body(function, function.body, type_stack)

    def _get_struct_field_type(
        self,
        function: Function,
        node: StructFieldQuery | StructFieldUpdate,
        struct_type: Type,
    ) -> VariableType:
        field_name = node.field_name.value
        try:
            field_type = struct_type.fields[field_name]
        except KeyError as e:
            raise UnknownField(
                position=node.position,
                function=function,
                struct_type=struct_type,
                field_name=field_name,
            ) from e

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
                position=field_query.position,
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

        # pop struct and field name, push field
        return type_stack[:-2] + [field_type]

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
                position=field_update.position,
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
                position=field_update.position,
                function=function,
                type_stack=type_stack,
                type_stack_before=type_stack_before,
            )

        field_type = self._get_struct_field_type(function, field_update, struct_type)

        if field_type != update_expr_type:
            raise StructUpdateTypeError(
                position=field_update.new_value_expr.position,
                function=function,
                type_stack=type_stack,
                struct_type=struct_type,
                field_name=field_update.field_name.value,
                found_type=update_expr_type,
                expected_type=field_selector_type,
            )

        # pop struct, field name and new value
        return type_stack[:-3]

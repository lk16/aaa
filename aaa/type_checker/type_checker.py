from copy import copy
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from aaa import AaaRunnerException, Position
from aaa.cross_referencer.models import (
    BooleanLiteral,
    Branch,
    CallArgument,
    CallFunction,
    CallType,
    CrossReferencerOutput,
    ForeachLoop,
    Function,
    FunctionBody,
    IntegerLiteral,
    StringLiteral,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
    VariableType,
    WhileLoop,
)
from aaa.type_checker.exceptions import (
    BranchTypeError,
    ConditionTypeError,
    ForeachLoopTypeError,
    FunctionTypeError,
    InvalidIterable,
    InvalidIterator,
    InvalidMainSignuture,
    InvalidMemberFunctionSignature,
    InvalidTestSignuture,
    MainFunctionNotFound,
    MissingIterable,
    StackTypesError,
    StructUpdateStackError,
    StructUpdateTypeError,
    TypeCheckerException,
    UnknownField,
    WhileLoopTypeError,
)
from aaa.type_checker.models import TypeCheckerOutput


class TypeChecker:
    def __init__(
        self, cross_referencer_output: CrossReferencerOutput, verbose: bool
    ) -> None:
        self.functions = cross_referencer_output.functions
        self.types = cross_referencer_output.types
        self.imports = cross_referencer_output.imports
        self.builtins_path = cross_referencer_output.builtins_path
        self.entrypoint = cross_referencer_output.entrypoint
        self.exceptions: List[TypeCheckerException] = []
        self.foreach_loop_stacks: Dict[Position, List[VariableType]] = {}
        self.verbose = verbose  # TODO use

    def run(self) -> TypeCheckerOutput:
        for function in self.functions.values():
            if self._is_builtin(function):
                # builtins can't be type-checked
                continue

            checker = SingleFunctionTypeChecker(function, self)

            try:
                foreach_loop_stacks = checker.run()
            except TypeCheckerException as e:
                self.exceptions.append(e)
            else:
                self.foreach_loop_stacks.update(foreach_loop_stacks)

        try:
            self._check_main_function()
        except TypeCheckerException as e:
            self.exceptions.append(e)

        if self.exceptions:
            raise AaaRunnerException(self.exceptions)

        return TypeCheckerOutput(self.foreach_loop_stacks)

    def _is_builtin(self, function: Function) -> bool:
        return function.position.file == self.builtins_path

    def _check_main_function(self) -> None:
        try:
            function = self.functions[(self.entrypoint, "main")]
        except KeyError:
            raise MainFunctionNotFound(self.entrypoint)

        if not all(
            [
                len(function.arguments) == 0,
                len(function.return_types) == 0,
                len(function.type_params) == 0,
            ]
        ):
            raise InvalidMainSignuture(function.position, function)


class SingleFunctionTypeChecker:
    def __init__(self, function: Function, type_checker: TypeChecker) -> None:
        self.function = function

        self.types = type_checker.types
        self.functions = type_checker.functions
        self.builtins_path = type_checker.builtins_path
        self.foreach_loop_stacks: Dict[Position, List[VariableType]] = {}

    def run(self) -> Dict[Position, List[VariableType]]:
        if self.function.is_test():
            self._check_test_function()

        if self.function.is_member_function():
            self._check_member_function()

        assert self.function.body
        computed_return_types = self._check_function_body(self.function.body, [])

        if computed_return_types != self.function.return_types:
            raise FunctionTypeError(self.function, computed_return_types)

        return self.foreach_loop_stacks

    def _match_signature_items(
        self,
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
                    expected_param, param, placeholder_types
                )

                if not match_result:
                    return False

            return True

    def _update_return_type(
        self, return_type: VariableType, placeholder_types: Dict[str, VariableType]
    ) -> VariableType:
        if return_type.is_placeholder:
            if return_type.name not in placeholder_types:
                # TODO
                raise NotImplementedError

            return placeholder_types[return_type.name]

        for i, param in enumerate(return_type.params):
            return_type.params[i] = self._update_return_type(param, placeholder_types)

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
        self, literal: IntegerLiteral, type_stack: List[VariableType]
    ) -> List[VariableType]:
        return type_stack + [self._get_int_var_type()]

    def _check_string_literal(
        self, literal: StringLiteral, type_stack: List[VariableType]
    ) -> List[VariableType]:
        return type_stack + [self._get_str_var_type()]

    def _check_boolean_literal(
        self,
        literal: BooleanLiteral,
        type_stack: List[VariableType],
    ) -> List[VariableType]:
        return type_stack + [self._get_bool_var_type()]

    def _check_condition(
        self, function_body: FunctionBody, type_stack: List[VariableType]
    ) -> None:
        # Condition is a special type of function body:
        # It should push exactly one boolean and not modify the type stack under it
        condition_stack = self._check_function_body(function_body, copy(type_stack))

        if condition_stack != type_stack + [self._get_bool_var_type()]:
            raise ConditionTypeError(
                function=self.function,
                position=function_body.position,
                type_stack=type_stack,
                condition_stack=condition_stack,
            )

    def _check_branch(
        self,
        branch: Branch,
        type_stack: List[VariableType],
    ) -> List[VariableType]:
        self._check_condition(branch.condition, copy(type_stack))

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for both the if- and else- bodies.
        if_stack = self._check_function_body(branch.if_body, copy(type_stack))

        if branch.else_body:
            else_stack = self._check_function_body(branch.else_body, copy(type_stack))
        else:
            else_stack = copy(type_stack)

        # Regardless whether the if- or else- branch is taken,
        # afterwards the stack should be the same.
        if if_stack != else_stack:
            raise BranchTypeError(
                position=branch.position,
                function=self.function,
                type_stack=type_stack,
                if_stack=if_stack,
                else_stack=else_stack,
            )

        # we can return either one, since they are the same
        return if_stack

    def _check_while_loop(
        self, while_loop: WhileLoop, type_stack: List[VariableType]
    ) -> List[VariableType]:
        self._check_condition(while_loop.condition, copy(type_stack))

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for the loop body.
        loop_stack = self._check_function_body(while_loop.body, copy(type_stack))

        if loop_stack != type_stack:
            raise WhileLoopTypeError(
                position=while_loop.position,
                function=self.function,
                type_stack=type_stack,
                loop_stack=loop_stack,
            )

        # we can return either one, since they are the same
        return loop_stack

    def _check_function_body(
        self, function_body: FunctionBody, type_stack: List[VariableType]
    ) -> List[VariableType]:

        checkers: Dict[Any, Callable[[Any, List[VariableType]], List[VariableType]]] = {
            BooleanLiteral: self._check_boolean_literal,
            Branch: self._check_branch,
            IntegerLiteral: self._check_integer_literal,
            WhileLoop: self._check_while_loop,
            StringLiteral: self._check_string_literal,
            StructFieldQuery: self._check_struct_field_query,
            StructFieldUpdate: self._check_struct_field_update,
            CallArgument: self._check_call_argument,
            CallFunction: self._check_call_function,
            CallType: self._check_call_type,
            ForeachLoop: self._check_foreach_loop,
        }

        stack = copy(type_stack)
        for item in function_body.items:
            stack = copy(stack)

            checker = checkers[type(item)]
            stack = checker(item, stack)

        return stack

    def _check_call_argument(
        self, call_arg: CallArgument, type_stack: List[VariableType]
    ) -> List[VariableType]:
        # Push argument on stack
        arg_var_type = call_arg.argument.var_type
        return type_stack + [arg_var_type]

    def _check_call_function(
        self, call_function: CallFunction, type_stack: List[VariableType]
    ) -> List[VariableType]:
        stack = copy(type_stack)
        arg_count = len(call_function.function.arguments)

        if len(stack) < arg_count:
            raise StackTypesError(
                function=self.function,
                type_stack=type_stack,
                func_like=call_function.function,
                position=call_function.position,
            )

        placeholder_types: Dict[str, VariableType] = {}
        types = stack[len(stack) - arg_count :]

        for argument, type in zip(call_function.function.arguments, types, strict=True):
            match_result = self._match_signature_items(
                argument.var_type, type, placeholder_types
            )

            if not match_result:
                raise StackTypesError(
                    function=self.function,
                    type_stack=type_stack,
                    func_like=call_function.function,
                    position=call_function.position,
                )

        stack = stack[: len(stack) - arg_count]

        for return_type in call_function.function.return_types:
            stack.append(self._update_return_type(return_type, placeholder_types))

        return stack

    def _check_call_type(
        self, call_type: CallType, type_stack: List[VariableType]
    ) -> List[VariableType]:
        return type_stack + [call_type.var_type]

    def _check_test_function(self) -> None:
        if not all(
            [
                len(self.function.arguments) == 0,
                len(self.function.return_types) == 0,
                len(self.function.type_params) == 0,
            ]
        ):
            raise InvalidTestSignuture(self.function)

    def _check_member_function(self) -> None:
        struct_type = self.types[
            (self.function.position.file, self.function.struct_name)
        ]

        # A member function on a type foo needs to take a foo object as the first argument
        if (
            len(self.function.arguments) == 0
            or self.function.arguments[0].var_type.type != struct_type
        ):
            raise InvalidMemberFunctionSignature(self.function, struct_type)

    def _get_struct_field_type(
        self, node: StructFieldQuery | StructFieldUpdate, struct_type: Type
    ) -> VariableType:
        field_name = node.field_name.value
        try:
            field_type = struct_type.fields[field_name]
        except KeyError as e:
            raise UnknownField(
                position=node.position,
                function=self.function,
                struct_type=struct_type,
                field_name=field_name,
            ) from e

        return field_type

    def _check_struct_field_query(
        self, field_query: StructFieldQuery, type_stack: List[VariableType]
    ) -> List[VariableType]:
        literal = StringLiteral(field_query.field_name)
        type_stack = self._check_string_literal(literal, copy(type_stack))

        if len(type_stack) < 2:
            raise StackTypesError(
                position=field_query.position,
                function=self.function,
                type_stack=type_stack,
                func_like=field_query,
            )

        struct_var_type, field_selector_type = type_stack[-2:]

        # This is enforced by the parser
        assert field_selector_type == self._get_str_var_type()

        field_type = self._get_struct_field_type(field_query, struct_var_type.type)

        # pop struct and field name, push field
        return type_stack[:-2] + [field_type]

    def _check_struct_field_update(
        self, field_update: StructFieldUpdate, type_stack: List[VariableType]
    ) -> List[VariableType]:
        literal = StringLiteral(field_update.field_name)
        type_stack = self._check_string_literal(literal, copy(type_stack))

        type_stack_before = type_stack
        type_stack = self._check_function_body(
            field_update.new_value_expr, copy(type_stack_before)
        )

        if len(type_stack) < 3:
            raise StackTypesError(
                position=field_update.position,
                function=self.function,
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
                function=self.function,
                type_stack=type_stack,
                type_stack_before=type_stack_before,
            )

        field_type = self._get_struct_field_type(field_update, struct_type)

        if field_type != update_expr_type:
            raise StructUpdateTypeError(
                position=field_update.new_value_expr.position,
                function=self.function,
                type_stack=type_stack,
                struct_type=struct_type,
                field_name=field_update.field_name.value,
                found_type=update_expr_type,
                expected_type=field_selector_type,
            )

        # pop struct, field name and new value
        return type_stack[:-3]

    def _lookup_function(
        self, var_type: VariableType, func_name: str
    ) -> Optional[Function]:
        # TODO this will fail if the function is defined in a different file than the type
        file = var_type.type.position.file
        name = f"{var_type.name}:{func_name}"
        return self.functions.get((file, name))

    def _check_foreach_loop(
        self, foreach_loop: ForeachLoop, type_stack: List[VariableType]
    ) -> List[VariableType]:
        self.foreach_loop_stacks[foreach_loop.position] = copy(type_stack)

        type_stack_before = copy(type_stack)

        if not type_stack:
            raise MissingIterable(foreach_loop.position, self.function)

        iterable_type = type_stack[-1]

        type_stack.append(iterable_type)

        iter_func = self._lookup_function(iterable_type, "iter")

        if not iter_func:
            raise InvalidIterable(foreach_loop.position, self.function, iterable_type)

        if not all(
            [
                len(iter_func.arguments) == 1,
                len(iter_func.return_types) == 1,
            ]
        ):
            raise InvalidIterable(foreach_loop.position, self.function, iterable_type)

        dummy_path = Position(Path("/dev/null"), -1, -1)
        call_function = CallFunction(iter_func, [], dummy_path)
        type_stack = self._check_call_function(call_function, type_stack)

        iterator_type = iter_func.return_types[0]
        next_func = self._lookup_function(iterator_type, "next")

        if not next_func:
            raise InvalidIterator(
                foreach_loop.position, self.function, iterable_type, iterator_type
            )

        if not all(
            [
                len(next_func.arguments) == 1,
                len(next_func.return_types) >= 2,
                next_func.return_types[-1] == self._get_bool_var_type(),
            ]
        ):
            raise InvalidIterator(
                foreach_loop.position, self.function, iterable_type, iterator_type
            )

        dummy_path = Position(Path("/dev/null"), -1, -1)
        call_function = CallFunction(next_func, [], dummy_path)

        type_stack = self._check_call_function(call_function, type_stack)
        type_stack.pop()
        type_stack = self._check_function_body(foreach_loop.body, type_stack)

        if type_stack != type_stack_before:
            raise ForeachLoopTypeError(
                foreach_loop.position, self.function, type_stack_before, type_stack
            )

        # pop iterable
        type_stack.pop()

        return type_stack

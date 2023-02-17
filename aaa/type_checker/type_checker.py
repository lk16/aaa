from copy import copy
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from aaa import AaaRunnerException, Position
from aaa.cross_referencer.models import (
    Assignment,
    BooleanLiteral,
    Branch,
    CallFunction,
    CallType,
    CallVariable,
    CrossReferencerOutput,
    ForeachLoop,
    Function,
    FunctionBody,
    IntegerLiteral,
    Never,
    Return,
    StringLiteral,
    StructFieldQuery,
    StructFieldUpdate,
    UseBlock,
    VariableType,
    WhileLoop,
)
from aaa.type_checker.exceptions import (
    AssignConstValueError,
    AssignmentTypeError,
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
    MemberFunctionTypeNotFound,
    MissingIterable,
    ReturnTypesError,
    SignatureItemMismatch,
    StackTypesError,
    StructUpdateStackError,
    StructUpdateTypeError,
    TypeCheckerException,
    UnknownField,
    UnreachableCode,
    UpdateConstStructError,
    UseBlockStackUnderflow,
    WhileLoopTypeError,
    format_typestack,
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
        self.verbose = verbose

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
                len(function.type_params) == 0,
            ]
        ):
            raise InvalidMainSignuture(function.position)

        if isinstance(function.return_types, Never):
            # It's fine if main never returns.
            return

        if len(function.return_types) != 0:
            raise InvalidMainSignuture(function.position)


class SingleFunctionTypeChecker:
    def __init__(self, function: Function, type_checker: TypeChecker) -> None:
        self.function = function

        self.types = type_checker.types
        self.functions = type_checker.functions
        self.builtins_path = type_checker.builtins_path
        self.foreach_loop_stacks: Dict[Position, List[VariableType]] = {}
        self.vars: Dict[str, VariableType] = {
            arg.name: arg.var_type for arg in function.arguments
        }
        self.verbose = type_checker.verbose

    def run(self) -> Dict[Position, List[VariableType]]:
        if self.function.is_test():  # pragma: nocover
            self._check_test_function()

        if self.function.is_member_function():
            self._check_member_function()

        assert self.function.body
        computed_return_types = self._check_function_body(self.function.body, [])

        if not self._confirm_return_types(computed_return_types):
            raise FunctionTypeError(self.function, computed_return_types)

        return self.foreach_loop_stacks

    def _confirm_return_types(self, computed: List[VariableType] | Never) -> bool:
        expected = self.function.return_types

        if isinstance(computed, Never):
            # If we never return, it doesn't matter what the signature promised to return.
            return True

        if isinstance(expected, Never):
            return False

        if len(expected) != len(computed):
            return False

        for expected_value, computed_value in zip(expected, computed):
            if computed_value.type is not expected_value.type:
                return False

            if computed_value.params != expected_value.params:
                return False

            if expected_value.is_const and not computed_value.is_const:
                return False

        return True

    def _match_signature_items(
        self,
        expected_var_type: VariableType,
        var_type: VariableType,
        placeholder_types: Dict[str, VariableType],
    ) -> Dict[str, VariableType]:
        if expected_var_type.is_placeholder:
            if expected_var_type.name in placeholder_types:
                if placeholder_types[expected_var_type.name] == var_type:
                    return placeholder_types
                raise SignatureItemMismatch

            placeholder_types[expected_var_type.name] = var_type
            return placeholder_types

        else:
            if expected_var_type.type is not var_type.type:
                raise SignatureItemMismatch

            if len(var_type.params) != len(expected_var_type.params):
                raise SignatureItemMismatch

            for expected_param, param in zip(expected_var_type.params, var_type.params):
                placeholder_types = self._match_signature_items(
                    expected_param, param, placeholder_types
                )

            if var_type.is_const and not expected_var_type.is_const:
                # Cannot use const value as non-const argument
                raise SignatureItemMismatch

            return placeholder_types

    def _update_return_type(
        self, return_type: VariableType, placeholder_types: Dict[str, VariableType]
    ) -> VariableType:
        if return_type.is_placeholder:
            updated_return_type = copy(placeholder_types[return_type.name])

            if return_type.is_const:
                updated_return_type.is_const = True

            return updated_return_type

        for i, param in enumerate(return_type.params):
            return_type.params[i] = self._update_return_type(param, placeholder_types)

        return return_type

    def _get_builtin_var_type(self, type_name: str) -> VariableType:
        type = self.types[(self.builtins_path, type_name)]
        return VariableType(type, [], False, type.position, False)

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
        self, literal: BooleanLiteral, type_stack: List[VariableType]
    ) -> List[VariableType]:
        return type_stack + [self._get_bool_var_type()]

    def _check_condition(
        self, function_body: FunctionBody, type_stack: List[VariableType]
    ) -> List[VariableType] | Never:
        # Condition is a special type of function body:
        # It should push exactly one boolean and not modify the type stack under it
        condition_stack = self._check_function_body(function_body, copy(type_stack))

        if isinstance(condition_stack, Never):
            return Never()

        if condition_stack != type_stack + [self._get_bool_var_type()]:
            raise ConditionTypeError(
                function_body.position, type_stack, condition_stack
            )

        return condition_stack

    def _check_branch(
        self, branch: Branch, type_stack: List[VariableType]
    ) -> List[VariableType] | Never:
        condition_stack = self._check_condition(branch.condition, copy(type_stack))

        if isinstance(condition_stack, Never):
            return Never()

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for both the if- and else- bodies.
        if_stack = self._check_function_body(branch.if_body, copy(type_stack))

        if branch.else_body:
            else_stack = self._check_function_body(branch.else_body, copy(type_stack))
        else:
            else_stack = copy(type_stack)

        # If a branch doesn't return, the return type will be whatever the other one returns
        # This works even if neither branch returns
        if isinstance(if_stack, Never):
            return else_stack

        if isinstance(else_stack, Never):
            return if_stack

        # Regardless whether the if- or else- branch is taken,
        # afterwards the stack should be the same.
        if if_stack != else_stack:
            raise BranchTypeError(branch.position, type_stack, if_stack, else_stack)

        # we can return either one, since they are the same
        return if_stack

    def _check_while_loop(
        self, while_loop: WhileLoop, type_stack: List[VariableType]
    ) -> List[VariableType] | Never:
        condition_stack = self._check_condition(while_loop.condition, copy(type_stack))

        if isinstance(condition_stack, Never):
            return Never()

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for the loop body.
        loop_stack = self._check_function_body(while_loop.body, copy(type_stack))

        if isinstance(loop_stack, Never):
            # NOTE: If the loop returns and the loop_stack does not,
            # that means the loop body never ran.
            return type_stack

        if loop_stack != type_stack:
            raise WhileLoopTypeError(while_loop.position, type_stack, loop_stack)

        return loop_stack

    def _print_types(
        self, position: Position, type_stack: List[VariableType] | Never
    ) -> None:  # pragma: nocover
        if not self.verbose:
            return

        formatted_position = str(position)
        formatted_stack = format_typestack(type_stack)

        if len(formatted_position) > 40:
            formatted_position = "…" + formatted_position[-39:]

        print(f"type checker | {formatted_position:>40} | {formatted_stack}")

    def _check_function_body(
        self, function_body: FunctionBody, type_stack: List[VariableType]
    ) -> List[VariableType] | Never:

        checkers: Dict[
            Any, Callable[[Any, List[VariableType]], List[VariableType] | Never]
        ] = {
            Assignment: self._check_assignment,
            BooleanLiteral: self._check_boolean_literal,
            Branch: self._check_branch,
            CallFunction: self._check_call_function,
            CallType: self._check_call_type,
            CallVariable: self._check_call_variable,
            ForeachLoop: self._check_foreach_loop,
            IntegerLiteral: self._check_integer_literal,
            Return: self._check_return,
            StringLiteral: self._check_string_literal,
            StructFieldQuery: self._check_struct_field_query,
            StructFieldUpdate: self._check_struct_field_update,
            UseBlock: self._check_use_block,
            WhileLoop: self._check_while_loop,
        }

        stack = copy(type_stack)
        for item_offset, item in enumerate(function_body.items):
            stack = copy(stack)

            checker = checkers[type(item)]
            checked = checker(item, stack)

            if isinstance(checked, Never):
                # Items following an item that never returns are dead code
                if item_offset != len(function_body.items) - 1:
                    next_item = function_body.items[item_offset + 1]
                    raise UnreachableCode(next_item.position)

                self._print_types(item.position, Never())
                return Never()

            stack = checked
            self._print_types(item.position, stack)

        return stack

    def _check_return(self, return_: Return, type_stack: List[VariableType]) -> Never:
        if not self._confirm_return_types(type_stack):
            raise ReturnTypesError(return_.position, type_stack, self.function)

        return Never()

    def _check_call_variable(
        self, call_var: CallVariable, type_stack: List[VariableType]
    ) -> List[VariableType]:
        # Push variable on stack
        type = self.vars[call_var.name]
        return type_stack + [type]

    def _simplify_stack_item(self, var_type: VariableType) -> VariableType:
        if (
            var_type.type.name == "remove_const"
            and var_type.type.position.file == self.builtins_path
        ):
            assert len(var_type.params) == 1

            var_type = copy(var_type.params[0])
            var_type.is_const = False

        return var_type

    def _check_call_function(
        self, call_function: CallFunction, type_stack: List[VariableType]
    ) -> List[VariableType] | Never:
        stack = copy(type_stack)
        arg_count = len(call_function.function.arguments)

        if len(stack) < arg_count:
            raise StackTypesError(
                call_function.position, type_stack, call_function.function
            )

        placeholder_types: Dict[str, VariableType] = {}
        types = stack[len(stack) - arg_count :]

        for argument, type in zip(call_function.function.arguments, types, strict=True):

            try:
                placeholder_types = self._match_signature_items(
                    argument.var_type, type, placeholder_types
                )
            except SignatureItemMismatch as e:
                raise StackTypesError(
                    call_function.position, type_stack, call_function.function
                ) from e

        stack = stack[: len(stack) - arg_count]

        if isinstance(call_function.function.return_types, Never):
            return Never()

        for return_type in call_function.function.return_types:
            stack_item = self._update_return_type(return_type, placeholder_types)
            stack_item = self._simplify_stack_item(stack_item)

            stack.append(stack_item)

        return stack

    def _check_call_type(
        self, call_type: CallType, type_stack: List[VariableType]
    ) -> List[VariableType]:
        return type_stack + [call_type.var_type]

    def _check_test_function(self) -> None:
        if isinstance(self.function.return_types, Never):
            raise InvalidTestSignuture(self.function)

        if not all(
            [
                len(self.function.arguments) == 0,
                len(self.function.return_types) == 0,
                len(self.function.type_params) == 0,
            ]
        ):
            raise InvalidTestSignuture(self.function)

    def _check_member_function(self) -> None:
        struct_type_key = (self.function.position.file, self.function.struct_name)

        try:
            struct_type = self.types[struct_type_key]
        except KeyError:
            raise MemberFunctionTypeNotFound(self.function)

        # A member function on a type foo needs to take a foo object as the first argument
        if (
            len(self.function.arguments) == 0
            or self.function.arguments[0].var_type.type != struct_type
        ):
            raise InvalidMemberFunctionSignature(self.function, struct_type)

    def _get_struct_field_type(
        self, node: StructFieldQuery | StructFieldUpdate, struct_var_type: VariableType
    ) -> VariableType:
        struct_type = struct_var_type.type

        field_name = node.field_name.value
        try:
            field_type = struct_type.fields[field_name]
        except KeyError as e:
            raise UnknownField(node.position, struct_type, field_name) from e

        if struct_var_type.is_const:
            field_type = copy(field_type)
            field_type.is_const = True

        return field_type

    def _check_struct_field_query(
        self, field_query: StructFieldQuery, type_stack: List[VariableType]
    ) -> List[VariableType]:
        literal = StringLiteral(field_query.field_name)
        type_stack = self._check_string_literal(literal, copy(type_stack))

        if len(type_stack) < 2:
            raise StackTypesError(field_query.position, type_stack, field_query)

        struct_var_type, field_selector_type = type_stack[-2:]

        # This is enforced by the parser
        assert field_selector_type == self._get_str_var_type()

        field_type = self._get_struct_field_type(field_query, struct_var_type)

        # pop struct and field name, push field
        return type_stack[:-2] + [field_type]

    def _check_struct_field_update(
        self, field_update: StructFieldUpdate, type_stack: List[VariableType]
    ) -> List[VariableType] | Never:
        literal = StringLiteral(field_update.field_name)
        type_stack = self._check_string_literal(literal, copy(type_stack))

        type_stack_before = type_stack
        type_stack_after = self._check_function_body(
            field_update.new_value_expr, copy(type_stack_before)
        )

        if isinstance(type_stack_after, Never):
            return type_stack_after

        type_stack = type_stack_after

        if len(type_stack) < 3:
            raise StackTypesError(field_update.position, type_stack, field_update)

        struct_var_type, field_selector_type, update_expr_type = type_stack[-3:]
        struct_type = struct_var_type.type

        if not all(
            [
                len(type_stack_before) == len(type_stack) - 1,
                type_stack_before == type_stack[:-1],
            ]
        ):
            raise StructUpdateStackError(
                field_update.position, type_stack, type_stack_before
            )

        if struct_var_type.is_const:
            raise UpdateConstStructError(field_update, struct_type.name)

        field_type = self._get_struct_field_type(field_update, struct_var_type)

        if field_type != update_expr_type:
            raise StructUpdateTypeError(
                position=field_update.new_value_expr.position,
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
        # NOTE It is required that member funcitions are
        # defined in same file as the type they operate on.
        file = var_type.type.position.file
        name = f"{var_type.name}:{func_name}"
        return self.functions.get((file, name))

    def _check_foreach_loop(
        self, foreach_loop: ForeachLoop, type_stack: List[VariableType]
    ) -> List[VariableType] | Never:
        self.foreach_loop_stacks[foreach_loop.position] = copy(type_stack)

        type_stack_before = copy(type_stack)

        if not type_stack:
            raise MissingIterable(foreach_loop.position)

        iterable_type = type_stack[-1]

        type_stack.append(iterable_type)

        if iterable_type.is_const:
            iter_func = self._lookup_function(iterable_type, "const_iter")
        else:
            iter_func = self._lookup_function(iterable_type, "iter")

        if not iter_func:
            raise InvalidIterable(foreach_loop.position, iterable_type)

        if isinstance(iter_func.return_types, Never):
            raise InvalidIterable(foreach_loop.position, iterable_type)

        if not all(
            [
                len(iter_func.arguments) == 1,
                len(iter_func.return_types) == 1,
            ]
        ):
            raise InvalidIterable(foreach_loop.position, iterable_type)

        dummy_path = Position(Path("/dev/null"), -1, -1)
        call_function = CallFunction(iter_func, [], dummy_path)
        type_stack_after_iter = self._check_call_function(call_function, type_stack)

        assert isinstance(type_stack_after_iter, list)  # This was checked earlier
        type_stack = type_stack_after_iter

        iterator_type = iter_func.return_types[0]
        next_func = self._lookup_function(iterator_type, "next")

        if not next_func:
            raise InvalidIterator(foreach_loop.position, iterable_type, iterator_type)

        if isinstance(next_func.return_types, Never):
            raise InvalidIterator(foreach_loop.position, iterable_type, iterator_type)

        if not all(
            [
                len(next_func.arguments) == 1,
                len(next_func.return_types) >= 2,
                next_func.return_types[-1] == self._get_bool_var_type(),
            ]
        ):
            raise InvalidIterator(foreach_loop.position, iterable_type, iterator_type)

        if iterable_type.is_const:
            for return_type in next_func.return_types[:-1]:
                if not return_type.is_const:
                    raise InvalidIterator(
                        foreach_loop.position, iterable_type, iterator_type
                    )

        dummy_path = Position(Path("/dev/null"), -1, -1)
        call_function = CallFunction(next_func, [], dummy_path)

        type_stack_after_next = self._check_call_function(call_function, type_stack)

        assert isinstance(type_stack_after_next, list)  # This was checked earlier
        type_stack = type_stack_after_next

        type_stack.pop()
        type_stack_after = self._check_function_body(foreach_loop.body, type_stack)

        if isinstance(type_stack_after, Never):
            return Never()

        type_stack = type_stack_after

        if type_stack != type_stack_before:
            raise ForeachLoopTypeError(
                foreach_loop.position, type_stack_before, type_stack
            )

        # pop iterable
        type_stack.pop()

        return type_stack

    def _check_use_block(
        self, use_block: UseBlock, type_stack: List[VariableType]
    ) -> List[VariableType] | Never:

        use_var_count = len(use_block.variables)

        if len(type_stack) < use_var_count:
            raise UseBlockStackUnderflow(len(type_stack), use_block)

        for var, type_stack_item in zip(
            use_block.variables, type_stack[-use_var_count:], strict=True
        ):
            self.vars[var.name] = type_stack_item

        type_stack = type_stack[:-use_var_count]
        return self._check_function_body(use_block.body, type_stack)

    def _check_assignment(
        self, assignment: Assignment, type_stack: List[VariableType]
    ) -> List[VariableType] | Never:
        assign_stack = self._check_function_body(assignment.body, [])

        expected_var_types: List[VariableType] = []

        for var in assignment.variables:
            type = self.vars[var.name]

            if type.is_const:
                raise AssignConstValueError(var, type)

            expected_var_types.append(type)

        if isinstance(assign_stack, Never):
            return Never()

        if len(assign_stack) != len(expected_var_types):
            raise AssignmentTypeError(expected_var_types, assign_stack, assignment)

        for expected, found in zip(expected_var_types, assign_stack, strict=True):
            if expected != found:
                raise AssignmentTypeError(expected_var_types, assign_stack, assignment)

        return type_stack

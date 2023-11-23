from copy import copy, deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple, Type

from aaa import Position
from aaa.cross_referencer.models import (
    Argument,
    Assignment,
    BooleanLiteral,
    Branch,
    CallEnumConstructor,
    CallFunction,
    CallFunctionByPointer,
    CallType,
    CallVariable,
    CaseBlock,
    CharacterLiteral,
    CrossReferencerOutput,
    DefaultBlock,
    Enum,
    EnumConstructor,
    ForeachLoop,
    Function,
    FunctionBody,
    FunctionBodyItem,
    FunctionPointer,
    GetFunctionPointer,
    IntegerLiteral,
    MatchBlock,
    Never,
    Return,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    UseBlock,
    Variable,
    VariableType,
    WhileLoop,
)
from aaa.runner.exceptions import AaaTranslationException
from aaa.type_checker.exceptions import (
    AssignConstValueError,
    AssignmentTypeError,
    BranchTypeError,
    CaseAsArgumentCountError,
    CaseEnumTypeError,
    CaseStackTypeError,
    CollidingVariable,
    ConditionTypeError,
    DuplicateCase,
    ForeachLoopTypeError,
    FunctionTypeError,
    InvalidCallWithTypeParameters,
    InvalidIterable,
    InvalidIterator,
    InvalidMainSignuture,
    InvalidMemberFunctionSignature,
    InvalidTestSignuture,
    MainFunctionNotFound,
    MatchTypeError,
    MemberFunctionTypeNotFound,
    MissingEnumCases,
    MissingIterable,
    ReturnTypesError,
    SignatureItemMismatch,
    StackTypesError,
    StructUpdateStackError,
    StructUpdateTypeError,
    TypeCheckerException,
    UnknownField,
    UnknownVariableOrFunction,
    UnreachableCode,
    UnreachableDefaultBlock,
    UpdateConstStructError,
    UseBlockStackUnderflow,
    UseFieldOfEnumException,
    UseFieldOfFunctionPointerException,
    WhileLoopTypeError,
    format_typestack,
)
from aaa.type_checker.models import TypeCheckerOutput


class TypeChecker:
    def __init__(
        self, cross_referencer_output: CrossReferencerOutput, verbose: bool
    ) -> None:
        self.functions = cross_referencer_output.functions
        self.types: Dict[Tuple[Path, str], Struct | Enum] = (
            cross_referencer_output.structs | cross_referencer_output.enums
        )
        self.imports = cross_referencer_output.imports
        self.builtins_path = cross_referencer_output.builtins_path
        self.entrypoint = cross_referencer_output.entrypoint
        self.exceptions: List[TypeCheckerException] = []
        self.position_stacks: Dict[
            Position, List[VariableType | FunctionPointer] | Never
        ] = {}
        self.verbose = verbose

    def run(self) -> TypeCheckerOutput:
        for function in self.functions.values():
            if self._is_builtin(function):
                # builtins can't be type-checked
                continue

            checker = SingleFunctionTypeChecker(function, self)

            try:
                checker.run()
            except TypeCheckerException as e:
                self.exceptions.append(e)
            finally:
                self.position_stacks.update(checker.position_stacks)

        self._print_position_stacks()

        try:
            self._check_main_function()
        except TypeCheckerException as e:
            self.exceptions.append(e)

        if self.exceptions:
            raise AaaTranslationException(self.exceptions)

        return TypeCheckerOutput(self.position_stacks)

    def _print_position_stacks(self) -> None:
        if not self.verbose:
            return

        for position in sorted(self.position_stacks.keys()):
            type_stack: List[
                VariableType | FunctionPointer
            ] | Never = self.position_stacks[position]

            formatted_position = str(position)
            formatted_stack = format_typestack(type_stack)

            if len(formatted_position) > 40:
                formatted_position = "…" + formatted_position[-39:]

            print(f"type checker | {formatted_position:>40} | {formatted_stack}")

    def _is_builtin(self, function: Function) -> bool:
        return function.position.file == self.builtins_path

    def _check_main_function(self) -> None:
        try:
            function = self.functions[(self.entrypoint, "main")]
        except KeyError:
            raise MainFunctionNotFound(self.entrypoint)

        main_arguments_ok = False

        if len(function.arguments) == 0:
            main_arguments_ok = True

        if (
            len(function.arguments) == 1
            and isinstance(function.arguments[0].type, VariableType)
            and function.arguments[0].type.name == "vec"
            and len(function.arguments[0].type.params) == 1
            and isinstance(function.arguments[0].type.params[0], VariableType)
            and function.arguments[0].type.params[0].name == "str"
        ):
            main_arguments_ok = True

        main_return_type_ok = False

        if isinstance(function.return_types, Never):
            # It's fine if main never returns.
            main_return_type_ok = True
        else:
            if len(function.return_types) == 0:
                main_return_type_ok = True

            if (
                len(function.return_types) == 1
                and isinstance(function.return_types[0], VariableType)
                and function.return_types[0].name == "int"
            ):
                main_return_type_ok = True

        if not all(
            [
                main_arguments_ok,
                main_return_type_ok,
                len(function.type_params) == 0,
            ]
        ):
            raise InvalidMainSignuture(function.position)


class SingleFunctionTypeChecker:
    def __init__(self, function: Function, type_checker: TypeChecker) -> None:
        self.function = function

        self.types = type_checker.types
        self.functions = type_checker.functions
        self.builtins_path = type_checker.builtins_path
        self.vars: Dict[
            str, Tuple[Variable | Argument, VariableType | FunctionPointer]
        ] = {arg.name: (arg, arg.type) for arg in function.arguments}
        self.verbose = type_checker.verbose

        # NOTE: we keep track of stacks per position.
        # This is useful for the Transpiler and for debugging.
        self.position_stacks: Dict[
            Position, List[VariableType | FunctionPointer] | Never
        ] = {}

    def run(self) -> None:
        assert self.function.body

        if self.function.is_test():  # pragma: nocover
            self._check_test_function()

        if self.function.is_member_function():
            self._check_member_function()

        computed_return_types = self._check_function_body(self.function.body, [])

        function_end_position = self.function.end_position
        assert function_end_position

        # NOTE: add computed return types so we can log it for debugging
        self.position_stacks[function_end_position] = computed_return_types

        if not self._confirm_return_types(computed_return_types):
            raise FunctionTypeError(self.function, computed_return_types)

    def _confirm_return_types(
        self, computed: List[VariableType | FunctionPointer] | Never
    ) -> bool:
        expected = self.function.return_types

        if isinstance(computed, Never):
            # If we never return, it doesn't matter what the signature promised to return.
            return True

        if isinstance(expected, Never):
            return False

        if len(expected) != len(computed):
            return False

        for expected_value, computed_value in zip(expected, computed):
            if isinstance(expected_value, VariableType):
                if not isinstance(computed_value, VariableType):
                    return False

                if computed_value.type != expected_value.type:
                    return False

                if computed_value.params != expected_value.params:
                    return False

                if expected_value.is_const and not computed_value.is_const:
                    return False
            else:
                assert isinstance(expected_value, FunctionPointer)
                if not isinstance(computed_value, FunctionPointer):
                    return False

                if computed_value.argument_types != expected_value.argument_types:
                    return False

                if computed_value.return_types != expected_value.return_types:
                    return False
        return True

    def _match_signature_items(
        self,
        expected_var_type: VariableType | FunctionPointer,
        var_type: VariableType | FunctionPointer,
        placeholder_types: Dict[str, VariableType | FunctionPointer],
    ) -> Dict[str, VariableType | FunctionPointer]:
        if isinstance(expected_var_type, FunctionPointer):
            if not isinstance(var_type, FunctionPointer):
                raise SignatureItemMismatch

            if expected_var_type != var_type:
                raise SignatureItemMismatch

            return placeholder_types

        if expected_var_type.is_placeholder:
            if expected_var_type.name in placeholder_types:
                if placeholder_types[expected_var_type.name] == var_type:
                    return placeholder_types
                raise SignatureItemMismatch

            placeholder_types[expected_var_type.name] = var_type
            return placeholder_types

        else:
            if not isinstance(var_type, VariableType):
                raise SignatureItemMismatch

            if expected_var_type.type != var_type.type:
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

    def _apply_placeholders_in_type(
        self,
        type: VariableType | FunctionPointer,
        placeholder_types: Mapping[str, VariableType | FunctionPointer],
    ) -> VariableType | FunctionPointer:
        if isinstance(type, FunctionPointer):
            # TODO #154 Support using function parameters in function pointer values
            return type

        type = deepcopy(type)

        if type.is_placeholder:
            updated_return_type = copy(placeholder_types[type.name])

            if isinstance(updated_return_type, VariableType) and type.is_const:
                updated_return_type.is_const = True

            return updated_return_type

        for i, param in enumerate(type.params):
            type.params[i] = self._apply_placeholders_in_type(param, placeholder_types)

        return type

    def _get_builtin_var_type(self, type_name: str) -> VariableType:
        type = self.types[(self.builtins_path, type_name)]
        return VariableType(type, [], False, type.position, False)

    def _get_bool_var_type(self) -> VariableType:
        return self._get_builtin_var_type("bool")

    def _get_str_var_type(self) -> VariableType:
        return self._get_builtin_var_type("str")

    def _get_char_var_type(self) -> VariableType:
        return self._get_builtin_var_type("char")

    def _get_int_var_type(self) -> VariableType:
        return self._get_builtin_var_type("int")

    def _check_integer_literal(
        self, literal: IntegerLiteral, type_stack: List[VariableType | FunctionPointer]
    ) -> List[VariableType | FunctionPointer]:
        return type_stack + [self._get_int_var_type()]

    def _check_string_literal(
        self, literal: StringLiteral, type_stack: List[VariableType | FunctionPointer]
    ) -> List[VariableType | FunctionPointer]:
        return type_stack + [self._get_str_var_type()]

    def _check_character_literal(
        self,
        literal: CharacterLiteral,
        type_stack: List[VariableType | FunctionPointer],
    ) -> List[VariableType | FunctionPointer]:
        return type_stack + [self._get_char_var_type()]

    def _check_boolean_literal(
        self, literal: BooleanLiteral, type_stack: List[VariableType | FunctionPointer]
    ) -> List[VariableType | FunctionPointer]:
        return type_stack + [self._get_bool_var_type()]

    def _check_get_function_pointer(
        self,
        get_func_ptr: GetFunctionPointer,
        type_stack: List[VariableType | FunctionPointer],
    ) -> List[VariableType | FunctionPointer]:
        target = get_func_ptr.target

        argument_types: List[VariableType | FunctionPointer] | Never
        return_types: List[VariableType | FunctionPointer] | Never

        if isinstance(target, Function):
            argument_types = [arg.type for arg in target.arguments]
            return_types = target.return_types
        else:
            assert isinstance(target, EnumConstructor)
            argument_types = target.enum.variants[target.variant_name]
            enum_var_type = VariableType(target.enum, [], False, target.position, False)
            return_types = [enum_var_type]

        func_ptr = FunctionPointer(get_func_ptr.position, argument_types, return_types)

        return type_stack + [func_ptr]

    def _check_condition(
        self,
        function_body: FunctionBody,
        type_stack: List[VariableType | FunctionPointer],
    ) -> List[VariableType | FunctionPointer] | Never:
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
        self, branch: Branch, type_stack: List[VariableType | FunctionPointer]
    ) -> List[VariableType | FunctionPointer] | Never:
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
        self, while_loop: WhileLoop, type_stack: List[VariableType | FunctionPointer]
    ) -> List[VariableType | FunctionPointer] | Never:
        condition_stack = self._check_condition(while_loop.condition, copy(type_stack))

        if isinstance(condition_stack, Never):
            return Never()

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for the loop body.
        body_stack = self._check_function_body(while_loop.body, copy(type_stack))

        if isinstance(body_stack, Never):
            return Never()

        if body_stack != type_stack:
            raise WhileLoopTypeError(while_loop.position, type_stack, body_stack)

        condition_items = while_loop.condition.items

        if (
            len(condition_items) == 1
            and isinstance(condition_items[0], BooleanLiteral)
            and condition_items[0].value
        ):
            # We found a `while true` loop
            return Never()

        return body_stack

    def _check_function_body(
        self,
        function_body: FunctionBody,
        type_stack: List[VariableType | FunctionPointer],
    ) -> List[VariableType | FunctionPointer] | Never:
        checkers: Dict[
            Type[FunctionBodyItem],
            Callable[
                [Any, List[VariableType | FunctionPointer]],
                List[VariableType | FunctionPointer] | Never,
            ],
        ] = {
            Assignment: self._check_assignment,
            BooleanLiteral: self._check_boolean_literal,
            Branch: self._check_branch,
            CallFunction: self._check_call_function,
            CallType: self._check_call_type,
            CallVariable: self._check_call_variable,
            CallEnumConstructor: self._check_call_enum_constructor,
            CharacterLiteral: self._check_character_literal,
            ForeachLoop: self._check_foreach_loop,
            FunctionPointer: self._check_function_pointer,
            IntegerLiteral: self._check_integer_literal,
            Return: self._check_return,
            StringLiteral: self._check_string_literal,
            StructFieldQuery: self._check_struct_field_query,
            StructFieldUpdate: self._check_struct_field_update,
            UseBlock: self._check_use_block,
            WhileLoop: self._check_while_loop,
            MatchBlock: self._check_match_block,
            CallFunctionByPointer: self._check_call_by_function_pointer,
            GetFunctionPointer: self._check_get_function_pointer,
        }

        assert set(checkers.keys()) == set(FunctionBodyItem.__args__)  # type: ignore

        stack = copy(type_stack)
        for item_offset, item in enumerate(function_body.items):
            stack = copy(stack)

            self.position_stacks[item.position] = copy(stack)

            checker = checkers[type(item)]
            checked = checker(item, stack)

            if isinstance(checked, Never):
                # Items following an item that never returns are dead code
                if item_offset != len(function_body.items) - 1:
                    next_item = function_body.items[item_offset + 1]
                    raise UnreachableCode(next_item.position)

                return Never()

            stack = checked

        return stack

    def _check_case_block(
        self,
        block: CaseBlock,
        type_stack: List[VariableType | FunctionPointer],
        enum_type: Enum,
    ) -> List[VariableType | FunctionPointer] | Never:
        if block.enum_type != enum_type:
            raise CaseEnumTypeError(block, enum_type, block.enum_type)

        variant_name = block.variant_name

        # The variant name is checked in the cross referencer so it cannot fail here.
        associated_data = enum_type.variants[variant_name]

        if block.variables:
            if len(block.variables) != len(associated_data):
                raise CaseAsArgumentCountError(block, len(associated_data))

            for var, type_stack_item in zip(
                block.variables, associated_data, strict=True
            ):
                if var.name in self.vars:
                    raise CollidingVariable(var, self.vars[var.name][0])

                colliding = self._find_var_name_collision(var)

                if colliding:
                    raise CollidingVariable(var, colliding)

                self.vars[var.name] = (var, type_stack_item)

            # NOTE: all pushed associated data is immediately used so we don't modify block_type_stack

        else:
            type_stack += associated_data

        return_type_stack = self._check_function_body(block.body, type_stack)

        for var in block.variables:
            del self.vars[var.name]

        return return_type_stack

    def _get_block_type_stacks(
        self,
        match_block: MatchBlock,
        type_stack: List[VariableType | FunctionPointer],
        enum_type: Enum,
    ) -> Tuple[
        List[List[VariableType | FunctionPointer] | Never], Optional[DefaultBlock]
    ]:
        block_type_stacks: List[List[VariableType | FunctionPointer] | Never] = []
        found_default_block: Optional[DefaultBlock] = None

        for block in match_block.blocks:
            block_type_stack: List[VariableType | FunctionPointer] | Never = copy(
                type_stack[:-1]
            )
            assert not isinstance(block_type_stack, Never)

            if isinstance(block, CaseBlock):
                block_type_stack = self._check_case_block(
                    block, block_type_stack, enum_type
                )

            else:
                if found_default_block:
                    raise DuplicateCase(found_default_block, block)

                found_default_block = block
                block_type_stack = self._check_function_body(
                    block.body, block_type_stack
                )

            block_type_stacks.append(block_type_stack)
        return block_type_stacks, found_default_block

    def _check_match_block(
        self, match_block: MatchBlock, type_stack: List[VariableType | FunctionPointer]
    ) -> List[VariableType | FunctionPointer] | Never:
        try:
            matched_var_type = type_stack[-1]
        except IndexError:
            raise MatchTypeError(match_block, type_stack)

        if not isinstance(matched_var_type, VariableType):
            raise MatchTypeError(match_block, type_stack)

        if not isinstance(matched_var_type.type, Enum):
            raise MatchTypeError(match_block, type_stack)

        enum_type = matched_var_type.type

        found_enum_variants: Dict[str, CaseBlock] = {}

        for block in match_block.blocks:
            if isinstance(block, CaseBlock):
                if block.enum_type != enum_type:
                    raise CaseEnumTypeError(block, enum_type, block.enum_type)

                if block.variant_name in found_enum_variants:
                    colliding_case_block = found_enum_variants[block.variant_name]
                    raise DuplicateCase(colliding_case_block, block)

                found_enum_variants[block.variant_name] = block

        block_type_stacks, found_default_block = self._get_block_type_stacks(
            match_block, type_stack, enum_type
        )

        missing_enum_variants = set(enum_type.variants.keys()) - set(
            found_enum_variants.keys()
        )

        if missing_enum_variants and not found_default_block:
            raise MissingEnumCases(match_block, enum_type, missing_enum_variants)

        if not missing_enum_variants and found_default_block:
            raise UnreachableDefaultBlock(found_default_block)

        match_stack: Never | List[VariableType | FunctionPointer] = Never()

        for block_type_stack in block_type_stacks:
            if isinstance(block_type_stack, Never):
                continue

            if isinstance(match_stack, Never):
                match_stack = block_type_stack
                continue

            if match_stack != block_type_stack:
                raise CaseStackTypeError(match_block.blocks, block_type_stacks)

        return match_stack

    def _check_return(
        self, return_: Return, type_stack: List[VariableType | FunctionPointer]
    ) -> Never:
        if not self._confirm_return_types(type_stack):
            raise ReturnTypesError(return_.position, type_stack, self.function)

        return Never()

    def _check_call_variable(
        self, call_var: CallVariable, type_stack: List[VariableType | FunctionPointer]
    ) -> List[VariableType | FunctionPointer]:
        try:
            var_or_arg, var_type = self.vars[call_var.name]
        except KeyError:
            raise UnknownVariableOrFunction(call_var.name, call_var.position)

        if call_var.has_type_params:
            # Handles cases like:
            # fn foo { 0 use c { c[b] } }
            # fn foo args a as int { a[b] drop }
            raise InvalidCallWithTypeParameters(call_var, var_or_arg)

        # Push variable on stack
        return type_stack + [var_type]

    def __check_call_function(
        self,
        type_params: List[VariableType | FunctionPointer],
        arguments: List[VariableType | FunctionPointer],
        return_types: List[VariableType | FunctionPointer] | Never,
        call: Function | EnumConstructor | CallFunctionByPointer,
        position: Position,
        type_stack: List[VariableType | FunctionPointer],
    ) -> List[VariableType | FunctionPointer] | Never:
        error_types_stack = self.position_stacks[position]
        assert not isinstance(error_types_stack, Never)

        stack = copy(type_stack)
        arg_count = len(arguments)

        if len(stack) < arg_count:
            raise StackTypesError(position, error_types_stack, call)

        placeholder_types: Dict[str, VariableType | FunctionPointer] = {}

        if isinstance(call, Function):
            if len(type_params) == len(call.type_params):
                for type_param_name, type_param in zip(
                    call.type_param_names, type_params
                ):
                    placeholder_types[type_param_name] = type_param
            elif len(type_params) != 0:
                raise NotImplementedError  # Unreachable, should be caught by CrossReferencer

        types = stack[len(stack) - arg_count :]

        for argument, type in zip(arguments, types, strict=True):
            try:
                placeholder_types = self._match_signature_items(
                    argument, copy(type), placeholder_types
                )
            except SignatureItemMismatch as e:
                expected_stack_top_override: Optional[
                    List[VariableType | FunctionPointer]
                ] = None

                if isinstance(call, Function):
                    expected_stack_top_override = [
                        self._apply_placeholders_in_type(item.type, placeholder_types)
                        for item in call.arguments
                    ]

                raise StackTypesError(
                    position,
                    error_types_stack,
                    call,
                    type_params=type_params,
                    expected_stack_top_override=expected_stack_top_override,
                ) from e

        stack = stack[: len(stack) - arg_count]

        if isinstance(return_types, Never):
            return Never()

        for return_type in return_types:
            stack_item = self._apply_placeholders_in_type(
                return_type, placeholder_types
            )
            stack.append(stack_item)

        return stack

    def _check_call_function(
        self,
        call_function: CallFunction,
        type_stack: List[VariableType | FunctionPointer],
    ) -> List[VariableType | FunctionPointer] | Never:
        self.position_stacks[call_function.position] = copy(type_stack)

        arguments = [argument.type for argument in call_function.function.arguments]

        type_stack_afterwards = self.__check_call_function(
            call_function.type_params,
            arguments,
            call_function.function.return_types,
            call_function.function,
            call_function.position,
            type_stack,
        )

        called = call_function.function

        if called.position.file == self.builtins_path and called.name == "copy":
            assert isinstance(type_stack_afterwards, list)
            assert isinstance(type_stack_afterwards[-1], VariableType)
            type_stack_afterwards[-1].is_const = False

        return type_stack_afterwards

    def _check_call_by_function_pointer(
        self,
        call_by_func_ptr: CallFunctionByPointer,
        type_stack: List[VariableType | FunctionPointer],
    ) -> List[VariableType | FunctionPointer] | Never:
        self.position_stacks[call_by_func_ptr.position] = copy(type_stack)

        try:
            func_ptr = type_stack.pop()
        except IndexError:
            raise StackTypesError(
                call_by_func_ptr.position, copy(type_stack), call_by_func_ptr
            )

        if not isinstance(func_ptr, FunctionPointer):
            raise StackTypesError(
                call_by_func_ptr.position, type_stack + [func_ptr], call_by_func_ptr
            )

        return self.__check_call_function(
            [],
            func_ptr.argument_types,
            func_ptr.return_types,
            call_by_func_ptr,
            call_by_func_ptr.position,
            type_stack,
        )

    def _check_call_enum_constructor(
        self,
        call_enum_ctor: CallEnumConstructor,
        type_stack: List[VariableType | FunctionPointer],
    ) -> List[VariableType | FunctionPointer] | Never:
        self.position_stacks[call_enum_ctor.position] = copy(type_stack)

        enum = call_enum_ctor.enum_ctor.enum
        variant_name = call_enum_ctor.enum_ctor.variant_name
        variant_associated_data = enum.get_resolved().variants[variant_name]

        return self.__check_call_function(
            [],
            variant_associated_data,
            [call_enum_ctor.enum_var_type],
            call_enum_ctor.enum_ctor,
            call_enum_ctor.position,
            type_stack,
        )

    def _check_call_type(
        self, call_type: CallType, type_stack: List[VariableType | FunctionPointer]
    ) -> List[VariableType | FunctionPointer]:
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
            type = self.types[struct_type_key]
        except KeyError:
            raise MemberFunctionTypeNotFound(self.function)

        # A member function on a type foo needs to take a foo object as the first argument
        if not (
            len(self.function.arguments) >= 1
            and isinstance(self.function.arguments[0].type, VariableType)
            and self.function.arguments[0].type.type == type
        ):
            raise InvalidMemberFunctionSignature(self.function, type)

    def _get_struct_field_type(
        self,
        node: StructFieldQuery | StructFieldUpdate,
        struct_var_type: VariableType | FunctionPointer,
    ) -> VariableType | FunctionPointer:
        if isinstance(struct_var_type, FunctionPointer):
            raise UseFieldOfFunctionPointerException(node)

        struct = struct_var_type.type

        if isinstance(struct, Enum):
            raise UseFieldOfEnumException(node)

        field_name = node.field_name.value
        try:
            field_type = struct.fields[field_name]
        except KeyError as e:
            raise UnknownField(node.position, struct, field_name) from e

        if isinstance(field_type, FunctionPointer):
            return field_type

        if struct_var_type.is_const:
            field_type = copy(field_type)
            field_type.is_const = True

        struct_param_dict = struct.param_dict(struct_var_type)

        return self._apply_placeholders_in_type(field_type, struct_param_dict)

    def _check_struct_field_query(
        self,
        field_query: StructFieldQuery,
        type_stack: List[VariableType | FunctionPointer],
    ) -> List[VariableType | FunctionPointer]:
        literal = StringLiteral(field_query.field_name)
        self.position_stacks[literal.position] = copy(type_stack)

        self.position_stacks[field_query.operator_position] = copy(type_stack)

        if len(type_stack) < 1:
            raise StackTypesError(field_query.position, type_stack, field_query)

        struct_var_type = type_stack[-1]

        field_type = self._get_struct_field_type(field_query, struct_var_type)

        # pop struct and field name, push field
        return type_stack[:-1] + [field_type]

    def _check_struct_field_update(
        self,
        field_update: StructFieldUpdate,
        type_stack: List[VariableType | FunctionPointer],
    ) -> List[VariableType | FunctionPointer] | Never:
        literal = StringLiteral(field_update.field_name)
        self.position_stacks[literal.position] = copy(type_stack)

        type_stack_before = type_stack
        type_stack_after = self._check_function_body(
            field_update.new_value_expr, copy(type_stack_before)
        )
        self.position_stacks[field_update.operator_position] = copy(type_stack_after)

        if isinstance(type_stack_after, Never):
            return type_stack_after

        type_stack = type_stack_after

        if len(type_stack) < 2:
            raise StackTypesError(field_update.position, type_stack, field_update)

        struct_var_type, update_expr_type = type_stack[-2:]

        if isinstance(struct_var_type, FunctionPointer):
            raise UseFieldOfFunctionPointerException(field_update)

        struct_type = struct_var_type.type

        if isinstance(struct_type, Enum):
            raise UseFieldOfEnumException(field_update)

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
                expected_type=field_type,
            )

        # pop struct, field name and new value
        return type_stack[:-2]

    def _lookup_function(
        self, var_type: VariableType, func_name: str
    ) -> Optional[Function]:
        # NOTE It is required that member funcitions are
        # defined in same file as the type they operate on.
        file = var_type.type.position.file
        name = f"{var_type.name}:{func_name}"
        return self.functions.get((file, name))

    def _check_foreach_loop(
        self,
        foreach_loop: ForeachLoop,
        type_stack: List[VariableType | FunctionPointer],
    ) -> List[VariableType | FunctionPointer] | Never:
        type_stack_before_foreach = copy(type_stack)

        if not type_stack:
            raise MissingIterable(foreach_loop.position)

        iterable_type = type_stack[-1]

        if not isinstance(iterable_type, VariableType):
            raise InvalidIterable(foreach_loop.position, iterable_type)

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

        # duplicate iterator
        iterator_var_type = type_stack[-1]

        type_stack.append(iterator_var_type)

        iterator_type = iter_func.return_types[0]

        if not isinstance(iterator_type, VariableType):
            raise InvalidIterator(foreach_loop.position, iterable_type, iterator_type)

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
                if isinstance(return_type, VariableType) and not return_type.is_const:
                    raise InvalidIterator(
                        foreach_loop.position, iterable_type, iterator_type
                    )

        dummy_path = Position(Path("/dev/null"), -1, -1)
        call_function = CallFunction(next_func, [], dummy_path)

        type_stack_after_next = self._check_call_function(call_function, type_stack)

        assert isinstance(type_stack_after_next, list)  # This was checked earlier
        type_stack = type_stack_after_next

        # boolean return value from next gets consumed by foreach construct
        type_stack.pop()

        type_stack_after = self._check_function_body(foreach_loop.body, type_stack)

        if isinstance(type_stack_after, Never):
            return Never()

        # foreach consumes iterable
        expected_type_stack_after_foreach = type_stack_before_foreach[:-1] + [
            iterator_var_type
        ]

        if type_stack_after != expected_type_stack_after_foreach:
            raise ForeachLoopTypeError(
                foreach_loop.position,
                expected_type_stack_after_foreach,
                type_stack_after,
            )

        return type_stack_after[:-1]

    def _find_var_name_collision(
        self, var: Variable
    ) -> Struct | Enum | Function | None:
        builtins_key = (self.builtins_path, var.name)
        key = (self.function.position.file, var.name)

        if builtins_key in self.types:
            return self.types[builtins_key]
        if key in self.types:
            return self.types[key]

        if builtins_key in self.functions:
            return self.functions[builtins_key]
        if key in self.functions:
            return self.functions[key]

        return None

    def _check_use_block(
        self, use_block: UseBlock, type_stack: List[VariableType | FunctionPointer]
    ) -> List[VariableType | FunctionPointer] | Never:
        use_var_count = len(use_block.variables)

        if len(type_stack) < use_var_count:
            raise UseBlockStackUnderflow(len(type_stack), use_block)

        for var, type_stack_item in zip(
            use_block.variables, type_stack[-use_var_count:], strict=True
        ):
            if var.name in self.vars:
                raise CollidingVariable(var, self.vars[var.name][0])

            colliding = self._find_var_name_collision(var)

            if colliding:
                raise CollidingVariable(var, colliding)

            self.vars[var.name] = (var, type_stack_item)

        type_stack = type_stack[:-use_var_count]
        returned_type_stack = self._check_function_body(use_block.body, type_stack)

        for var in use_block.variables:
            del self.vars[var.name]

        return returned_type_stack

    def _check_assignment(
        self, assignment: Assignment, type_stack: List[VariableType | FunctionPointer]
    ) -> List[VariableType | FunctionPointer] | Never:
        assign_stack = self._check_function_body(assignment.body, [])

        expected_var_types: List[VariableType | FunctionPointer] = []

        for var in assignment.variables:
            try:
                _, type = self.vars[var.name]
            except KeyError:
                raise UnknownVariableOrFunction(var.name, var.position)

            if isinstance(type, VariableType):
                if type.is_const:
                    raise AssignConstValueError(var, type)
            else:
                assert isinstance(type, FunctionPointer)

            expected_var_types.append(type)

        if isinstance(assign_stack, Never):
            return Never()

        if len(assign_stack) != len(expected_var_types):
            raise AssignmentTypeError(expected_var_types, assign_stack, assignment)

        for expected, found in zip(expected_var_types, assign_stack, strict=True):
            if expected != found:
                raise AssignmentTypeError(expected_var_types, assign_stack, assignment)

        return type_stack

    def _check_function_pointer(
        self,
        func_ptr: FunctionPointer,
        type_stack: List[VariableType | FunctionPointer],
    ) -> List[VariableType | FunctionPointer]:
        return type_stack + [func_ptr]

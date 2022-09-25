from copy import copy, deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Tuple, Union

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
    MemberFunctionName,
    Operator,
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

DUMMY_TOKEN = Token(type_="", value="")  # type: ignore

DUMMY_TYPE_LITERAL = parser.TypeLiteral(
    identifier=parser.Identifier(name="str", token=DUMMY_TOKEN, file=Path("/dev/null")),
    params=parser.TypeParameters(value=[], token=DUMMY_TOKEN, file=Path("/dev/null")),
    token=DUMMY_TOKEN,
    file=Path("/dev/null"),
)


class TypeChecker:
    def __init__(self, cross_referencer_output: CrossReferencerOutput) -> None:
        self.identifiers = cross_referencer_output.identifiers
        self.builtins_path = cross_referencer_output.builtins_path
        self.signatures: Dict[Tuple[Path, str], Signature] = {}
        self.exceptions: List[TypeCheckerException] = []

    def run(self) -> TypeCheckerOutput:
        for (file, func_name), function in self.identifiers.items():
            if isinstance(function, Function):
                assert not isinstance(function.arguments, Unresolved)
                assert not isinstance(function.return_types, Unresolved)

                self.signatures[(file, func_name)] = Signature(
                    arguments=[arg.type for arg in function.arguments],
                    return_types=function.return_types,
                )

        for (file, _), function in self.identifiers.items():
            if isinstance(function, Function):
                self.function = function

                try:
                    self._check(file, function)
                except TypeCheckerException as e:
                    self.exceptions.append(e)

        return TypeCheckerOutput(exceptions=self.exceptions)

    def _check(self, file: Path, function: Function) -> None:
        if file == self.builtins_path:
            # builtins can't be type checked
            return

        key = function.identify()
        expected_return_types = self.signatures[key].return_types

        computed_return_types = self._check_function(file, function, [])

        if computed_return_types != expected_return_types:

            raise FunctionTypeError(
                file=file,
                token=function.token,
                function=function,
                expected_return_types=expected_return_types,
                computed_return_types=computed_return_types,
            )

    def _check_and_apply_signature(
        self,
        file: Path,
        function: Function,
        type_stack: List[VariableType],
        signature: Signature,
        func_like: Union[Operator, Function, MemberFunctionName],
    ) -> List[VariableType]:
        stack = copy(type_stack)
        arg_count = len(signature.arguments)

        if len(stack) < arg_count:
            raise StackTypesError(
                file=file,
                token=func_like.token,
                function=function,
                signature=signature,
                type_stack=type_stack,
                func_like=func_like,
            )

        placeholder_types: Dict[str, VariableType] = {}
        expected_types = signature.arguments
        types = stack[len(stack) - arg_count :]

        for expected_type, type in zip(expected_types, types, strict=True):
            match_result = self._match_signature_items(
                file, function, expected_type, type, placeholder_types
            )

            if not match_result:
                raise StackTypesError(
                    file=file,
                    token=func_like.token,
                    function=function,
                    signature=signature,
                    type_stack=type_stack,
                    func_like=func_like,
                )

        stack = stack[: len(stack) - arg_count]

        for return_type in signature.return_types:
            stack.append(
                self._update_return_type(
                    file, function, deepcopy(return_type), placeholder_types
                )
            )

        return stack

    def _match_signature_items(
        self,
        file: Path,
        function: Function,
        expected_type: VariableType,
        type: VariableType,
        placeholder_types: Dict[str, VariableType],
    ) -> bool:
        # TODO
        raise NotImplementedError

    def _update_return_type(
        self,
        file: Path,
        function: Function,
        return_type: VariableType,
        placeholder_types: Dict[str, VariableType],
    ) -> VariableType:
        # TODO
        raise NotImplementedError

    def _get_builtin_var_type(self, type_name: str) -> VariableType:
        type = self.identifiers[(self.builtins_path, type_name)]

        assert isinstance(type, Type)

        return VariableType(
            parsed=DUMMY_TYPE_LITERAL,
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
        file: Path,
        function: Function,
        function_body: FunctionBody,
        type_stack: List[VariableType],
    ) -> None:
        # Condition is a special type of function body:
        # It should push exactly one boolean and not modify the type stack under it
        condition_stack = self._check_function_body(
            file, function, function_body, copy(type_stack)
        )

        if condition_stack != type_stack + [self._get_bool_var_type()]:
            raise ConditionTypeError(
                file=file,
                token=function_body.token,
                function=function,
                type_stack=type_stack,
                condition_stack=condition_stack,
            )

    def _check_branch(
        self,
        file: Path,
        function: Function,
        branch: Branch,
        type_stack: List[VariableType],
    ) -> List[VariableType]:
        self._check_condition(file, function, branch.condition, copy(type_stack))

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for both the if- and else- bodies.
        if_stack = self._check_function_body(
            file, function, branch.if_body, copy(type_stack)
        )
        else_stack = self._check_function_body(
            file, function, branch.else_body, copy(type_stack)
        )

        # Regardless whether the if- or else- branch is taken,
        # afterwards the stack should be the same.
        if if_stack != else_stack:
            raise BranchTypeError(
                file=file,
                token=branch.token,
                function=function,
                type_stack=type_stack,
                if_stack=if_stack,
                else_stack=else_stack,
            )

        # we can return either one, since they are the same
        return if_stack

    def _check_loop(
        self, file: Path, function: Function, loop: Loop, type_stack: List[VariableType]
    ) -> List[VariableType]:
        self._check_condition(file, function, loop.condition, copy(type_stack))

        # The bool pushed by the condition is removed when evaluated,
        # so we can use type_stack as the stack for the loop body.
        loop_stack = self._check_function_body(
            file, function, loop.body, copy(type_stack)
        )

        if loop_stack != type_stack:
            raise LoopTypeError(
                file=file,
                token=loop.token,
                function=function,
                type_stack=type_stack,
                loop_stack=loop_stack,
            )

        # we can return either one, since they are the same
        return loop_stack

    def _check_function_body(
        self,
        file: Path,
        function: Function,
        function_body: FunctionBody,
        type_stack: List[VariableType],
    ) -> List[VariableType]:

        stack = copy(type_stack)
        for child_node in function_body.items:
            if isinstance(child_node, BooleanLiteral):
                stack = self._check_boolean_literal(copy(stack))
            elif isinstance(child_node, Branch):
                stack = self._check_branch(file, function, child_node, copy(stack))
            elif isinstance(child_node, IntegerLiteral):
                stack = self._check_integer_literal(copy(stack))
            elif isinstance(child_node, Loop):
                stack = self._check_loop(file, function, child_node, copy(stack))
            elif isinstance(child_node, MemberFunctionName):
                raise NotImplementedError
                # TODO or remove if we will treat member functions as functions
            elif isinstance(child_node, StringLiteral):
                stack = self._check_string_literal(copy(stack))
            elif isinstance(child_node, VariableType):
                stack = self._check_parsed_type(child_node, copy(stack))
            elif isinstance(child_node, StructFieldQuery):
                stack = self._check_type_struct_field_query(
                    file, function, child_node, copy(stack)
                )
            elif isinstance(child_node, StructFieldUpdate):
                stack = self._check_type_struct_field_update(
                    file, function, child_node, copy(stack)
                )
            elif isinstance(child_node, Identifier):
                stack = self._check_identifier(file, function, child_node, type_stack)
            else:  # pragma nocover
                assert False

        return stack

    def _check_identifier(
        self,
        file: Path,
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
            signature = self.signatures[called_function.identify()]
            return self._check_and_apply_signature(
                file, function, type_stack, signature, called_function
            )
        elif isinstance(identifier.kind, IdentifierCallingType):
            # TODO should identifier.kind.type be VariableType instead of Type?
            raise NotImplementedError
        else:  # pragma: nocover
            assert False

    def _check_function(
        self, file: Path, function: Function, type_stack: List[VariableType]
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
                    file=file,
                    token=function.token,
                    function=function,
                )

        if function.is_member_function():
            signature = self.signatures[function.identify()]
            struct_type = self.identifiers[function.identify()]

            assert isinstance(struct_type, Type)

            if TYPE_CHECKING:  # pragma: nocover
                assert isinstance(signature.arguments[0], VariableType)
                assert isinstance(signature.return_types[0], VariableType)

            # A memberfunction on a type foo needs to have foo as
            # type of thefirst argument and first return type
            if (
                len(signature.arguments) == 0
                or signature.arguments[0].type != struct_type
                or len(signature.return_types) == 0
                or signature.return_types[0].type != struct_type
            ):
                raise InvalidMemberFunctionSignature(
                    file=file,
                    token=function.token,
                    function=function,
                    struct_type=struct_type,
                    signature=signature,
                )

        assert not isinstance(function.body, Unresolved)
        return self._check_function_body(file, function, function.body, type_stack)

    def _get_struct_field_type(
        self,
        file: Path,
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
                file=file,
                token=node.token,
                function=function,
                struct_type=struct_type,
                field_name=field_name,
            ) from e

        assert not isinstance(field_type, Unresolved)
        return field_type

    def _check_type_struct_field_query(
        self,
        file: Path,
        function: Function,
        field_query: StructFieldQuery,
        type_stack: List[VariableType],
    ) -> List[VariableType]:
        type_stack = self._check_string_literal(copy(type_stack))

        if len(type_stack) < 2:
            raise StackTypesError(
                file=file,
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
            file, function, field_query, struct_var_type.type
        )

        type_stack.pop()
        type_stack.append(field_type)
        return type_stack

    def _check_type_struct_field_update(
        self,
        file: Path,
        function: Function,
        field_update: StructFieldUpdate,
        type_stack: List[VariableType],
    ) -> List[VariableType]:
        type_stack = self._check_string_literal(copy(type_stack))

        type_stack_before = type_stack
        type_stack = self._check_function_body(
            file, function, field_update.new_value_expr, copy(type_stack_before)
        )

        if len(type_stack) < 3:
            raise StackTypesError(
                file=file,
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
                file=file,
                token=field_update.token,
                function=function,
                type_stack=type_stack,
                type_stack_before=type_stack_before,
            )

        field_type = self._get_struct_field_type(
            file, function, field_update, struct_type
        )

        if field_type != update_expr_type:
            raise StructUpdateTypeError(
                file=file,
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

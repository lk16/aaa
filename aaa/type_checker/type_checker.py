from copy import copy, deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Tuple, Union

from aaa.cross_referencer.exceptions import CollidingIdentifier
from aaa.cross_referencer.models import (
    BooleanLiteral,
    Branch,
    CrossReferencerOutput,
    Function,
    FunctionBody,
    Identifier,
    IdentifierKind,
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
    LoopTypeError,
    SetFieldOfNonStructTypeError,
    StackTypesError,
    StructUpdateStackError,
    StructUpdateTypeError,
)
from aaa.type_checker.models import (
    Signature,
    StructQuerySignature,
    StructUpdateSignature,
)

DUMMY_TOKEN = Token(type_="", value="")  # type: ignore

DUMMY_TYPE_LITERAL = parser.TypeLiteral(
    identifier=Identifier(
        kind=IdentifierKind(),
        parsed=parser.Identifier(name="str", token=DUMMY_TOKEN),
    ),
    params=parser.TypeParameters(value=[], token=DUMMY_TOKEN),
    token=DUMMY_TOKEN,
)


class TypeChecker:
    def __init__(self, cross_referencer_output: CrossReferencerOutput) -> None:
        self.identifiers = cross_referencer_output.identifiers
        self.builtins_path = cross_referencer_output.builtins_path
        self.signatures: Dict[Tuple[Path, str], Signature] = {}

    def run(self) -> None:
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
                self._check(file, function)

    def _check(self, file: Path, function: Function) -> None:
        key = (file, function.identify())
        expected_return_types = self.signatures[key].return_types

        computed_return_types = self._check_function(file, function, [])

        if computed_return_types != expected_return_types:

            raise FunctionTypeError(
                file=file,
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
            name=type_name,
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
            else:  # pragma nocover
                assert False

        return stack

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
                    function=function,
                )

        if isinstance(function.name, MemberFunctionName):
            signature = self.program.get_signature(file, function)
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
                    file=file,
                    function=function,
                    struct=struct,
                    signature=signature,
                )

        for arg_offset, arg in enumerate(function.arguments):
            colliding_identifier = self.program.get_identifier(file, arg.name)

            if colliding_identifier:
                raise CollidingIdentifier(
                    file=file,
                    colliding=arg,
                    found=colliding_identifier,
                )

            if arg.name == function.name:
                raise CollidingIdentifier(file=file, colliding=arg, found=function)

            for preceding_arg in function.arguments[:arg_offset]:
                if arg.name == preceding_arg.name:
                    raise CollidingIdentifier(
                        file=file,
                        colliding=arg,
                        found=preceding_arg,
                    )

        return self._check_function_body(file, function, function.body, type_stack)

    def _get_struct_field_type(
        self,
        file: Path,
        function: Function,
        node: StructFieldQuery | StructFieldUpdate,
        struct_type: Type,
    ) -> VariableType:
        field_name = node.field_name.value

        try:
            return struct_type.fields[field_name]
        except KeyError as e:
            raise UnknownStructField(
                file=file,
                function=function,
                struct=struct_type,
                field_name=field_name,
            ) from e

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
                function=function,
                signature=StructQuerySignature(),
                type_stack=type_stack,
                func_like=field_query,
            )

        struct_type, field_selector_type = type_stack[-2:]

        # This is enforced by the parser
        assert field_selector_type.root_type == RootType.STRING

        if struct_type.root_type != RootType.STRUCT:
            raise GetFieldOfNonStructTypeError(
                file=file,
                type_stack=type_stack,
                function=function,
                field_query=field_query,
            )

        struct_name = struct_type.name

        # These should not raise, they are enforced by the Program class
        struct = self.program.identifiers[self.file][struct_name]
        assert isinstance(struct, Struct)

        field_type = self._get_struct_field_type(file, function, field_query, struct)

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
                function=function,
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
                file=file,
                function=function,
                type_stack=type_stack,
                type_stack_before=type_stack_before,
                field_update=field_update,
            )

        struct_name = struct_type.name

        if struct_type.root_type != RootType.STRUCT:
            raise SetFieldOfNonStructTypeError(
                file=file,
                type_stack=type_stack,
                function=function,
                field_update=field_update,
            )

        # These should not raise, they are enforced by the Program class
        struct = self.program.identifiers[self.file][struct_name]
        assert isinstance(struct, Struct)

        field_type = self._get_struct_field_type(file, function, field_update, struct)

        if field_type != update_expr_type:
            raise StructUpdateTypeError(
                file=file,
                function=function,
                type_stack=type_stack,
                struct_type=struct,
                field_name=field_update.field_name.value,
                found_type=update_expr_type,
                expected_type=field_selector_type,
                field_update=field_update,
            )

        # drop field_selector and update value
        return type_stack[:-2]

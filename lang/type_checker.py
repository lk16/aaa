from copy import copy
from dataclasses import dataclass
from typing import Callable, Dict, List, Type

from lang.parse import (
    AaaTreeNode,
    BooleanLiteral,
    Branch,
    Function,
    FunctionBody,
    Identifier,
    IntegerLiteral,
    Loop,
    Operator,
    StringLiteral,
)

StackItem = int | bool | str

TypeStack = List[Type[StackItem]]

IDENTIFIER_TO_TYPE: Dict[str, Type[StackItem]] = {
    "bool": bool,
    "int": int,
    "str": str,
}


@dataclass
class SomeType:
    name: str


SignatureItem = Type[StackItem] | SomeType


@dataclass
class Signature:
    arg_types: List[SignatureItem]
    return_types: List[SignatureItem]


# TODO test that keys match instructions.py and grammar
OPERATOR_SIGNATURES: Dict[str, List[Signature]] = {
    "+": [
        Signature([int, int], [bool]),
        Signature([str, str], [bool]),
    ],
    "-": [Signature([int, int], [int])],
    "*": [Signature([int, int], [int])],
    "/": [Signature([int, int], [int])],
    "%": [Signature([int, int], [int])],
    "and": [Signature([bool, bool], [bool])],
    "or": [Signature([bool, bool], [bool])],
    "not": [Signature([bool], [bool])],
    "nop": [Signature([], [])],
    "=": [
        Signature([int, int], [bool]),
        Signature([str, str], [str]),
    ],
    ">": [Signature([int, int], [int])],
    ">=": [Signature([int, int], [int])],
    "<": [Signature([int, int], [int])],
    "<=": [Signature([int, int], [int])],
    "!=": [
        Signature([int, int], [bool]),
        Signature([str, str], [bool]),
    ],
    "drop": [Signature([SomeType("a")], [])],
    "dup": [Signature([SomeType("a")], [SomeType("a"), SomeType("a")])],
    "swap": [
        Signature(
            [SomeType("a"), SomeType("b")],
            [SomeType("b"), SomeType("a")],
        )
    ],
    "over": [
        Signature(
            [SomeType("a"), SomeType("b")],
            [SomeType("a"), SomeType("b"), SomeType("a")],
        )
    ],
    "rot": [
        Signature(
            [SomeType("a"), SomeType("b"), SomeType("c")],
            [SomeType("b"), SomeType("c"), SomeType("a")],
        )
    ],
    "\\n": [Signature([], [])],
    ".": [
        Signature([bool], []),
        Signature([int], []),
        Signature([str], []),
    ],
    "substr": [Signature([str, int, int], [str])],
    "strlen": [Signature([str], [int])],
}


class TypeChecker:
    def __init__(self, function: Function) -> None:
        self.function = function

        self.type_check_funcs: Dict[
            Type[AaaTreeNode],
            Callable[[AaaTreeNode, TypeStack], TypeStack],
        ] = {
            IntegerLiteral: self.integer_literal_type_check,
            StringLiteral: self.string_literal_type_check,
            BooleanLiteral: self.boolean_literal_type_check,
            Operator: self.operator_type_check,
            Loop: self.loop_type_check,
            Identifier: self.identifier_type_check,
            Branch: self.branch_type_check,
            FunctionBody: self.function_body_type_check,
        }

    def check_types(self) -> None:
        type_stack: TypeStack = []

        for arg in self.function.arguments:
            assert not isinstance(arg.type, SomeType)
            type_stack.append(arg.type)

        return_types = self.function_body_type_check(self.function, type_stack)

        _ = return_types
        # TODO check if return_types match what self.function specifies
        raise NotImplementedError

    def check_and_apply_signature(
        self, type_stack: TypeStack, signature: Signature
    ) -> TypeStack:
        arg_count = len(signature.arg_types)

        if len(type_stack) < arg_count:
            raise NotImplementedError

        type_stack_under_args = type_stack[:-arg_count]
        type_stack_args = type_stack[-arg_count:]

        for arg_type, type_stack_arg in zip(signature.arg_types, type_stack_args):
            if type(arg_type) != type(type_stack_arg) and not isinstance(
                arg_type, SomeType
            ):
                raise NotImplementedError

        # TODO we should replace SomeArg by concrete types here
        returned_types: TypeStack = signature.return_types  # type: ignore

        return copy(type_stack_under_args) + returned_types

    def integer_literal_type_check(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        return type_stack + [int]

    def string_literal_type_check(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        return type_stack + [str]

    def boolean_literal_type_check(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        return type_stack + [bool]

    def operator_type_check(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        assert isinstance(node, Operator)
        signatures = OPERATOR_SIGNATURES[node.value]

        # TODO write loop
        assert len(signatures) == 1
        signature = signatures[0]

        return self.check_and_apply_signature(type_stack, signature)

    def loop_type_check(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        # TODO use copy on type_stack before checking children
        raise NotImplementedError

    def identifier_type_check(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        # TODO use copy on type_stack before checking children
        raise NotImplementedError

    def branch_type_check(self, node: AaaTreeNode, type_stack: TypeStack) -> TypeStack:
        # TODO use copy on type_stack before checking children
        raise NotImplementedError

    def function_body_type_check(
        self, node: AaaTreeNode, type_stack: TypeStack
    ) -> TypeStack:
        # TODO use copy on type_stack before checking children
        raise NotImplementedError

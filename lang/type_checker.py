from copy import copy
from typing import Callable, Dict, List, Tuple, Type

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
from lang.types import ArbitraryType, BaseType, Boolean, Integer, String

# TODO test that keys match instructions.py and grammar
# TODO use dataclass instead of tuple
# TODO use python types (and StackItem) instead of these classes
OPERATOR_SIGNATURES: Dict[str, List[Tuple[List[BaseType], List[BaseType]]]] = {
    "+": [
        ([Integer(), Integer()], [Boolean()]),
        ([String(), String()], [Boolean()]),
    ],
    "-": [([Integer(), Integer()], [Integer()])],
    "*": [([Integer(), Integer()], [Integer()])],
    "/": [([Integer(), Integer()], [Integer()])],
    "%": [([Integer(), Integer()], [Integer()])],
    "and": [([Boolean(), Boolean()], [Boolean()])],
    "or": [([Boolean(), Boolean()], [Boolean()])],
    "not": [([Boolean()], [Boolean()])],
    "nop": [([], [])],
    "=": [
        ([Integer(), Integer()], [Boolean()]),
        ([String(), String()], [Boolean()]),
    ],
    ">": [([Integer(), Integer()], [Boolean()])],
    ">=": [([Integer(), Integer()], [Boolean()])],
    "<": [([Integer(), Integer()], [Boolean()])],
    "<=": [([Integer(), Integer()], [Boolean()])],
    "!=": [
        ([Integer(), Integer()], [Boolean()]),
        ([String(), String()], [Boolean()]),
    ],
    "drop": [([ArbitraryType("a")], [])],
    "dup": [([ArbitraryType("a")], [ArbitraryType("a"), ArbitraryType("a")])],
    "swap": [
        (
            [ArbitraryType("a"), ArbitraryType("b")],
            [ArbitraryType("b"), ArbitraryType("a")],
        )
    ],
    "over": [
        (
            [ArbitraryType("a"), ArbitraryType("b")],
            [ArbitraryType("a"), ArbitraryType("b"), ArbitraryType("a")],
        )
    ],
    "rot": [
        (
            [ArbitraryType("a"), ArbitraryType("b"), ArbitraryType("c")],
            [ArbitraryType("b"), ArbitraryType("c"), ArbitraryType("a")],
        )
    ],
    "\\n": [([], [])],
    ".": [
        ([Boolean()], []),
        ([Integer()], []),
        ([String()], []),
    ],
    "substr": [([String(), Integer(), Integer()], [String()])],
    "strlen": [([String()], [Integer()])],
}


class TypeChecker:
    def __init__(self, function: Function) -> None:
        self.function = function

        self.type_check_funcs: Dict[
            Type[AaaTreeNode], Callable[[AaaTreeNode, List[BaseType]], List[BaseType]]
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
        type_stack = [arg.type for arg in self.function.arguments]
        return_types = self.function_body_type_check(self.function, type_stack)

        _ = return_types
        # TODO check if return_types match what self.function specifies
        raise NotImplementedError

    def check_and_apply_signature(
        self,
        type_stack: List[BaseType],
        arg_types: List[BaseType],
        return_types: List[BaseType],
    ) -> List[BaseType]:
        arg_count = len(arg_types)

        if len(type_stack) < arg_count:
            raise NotImplementedError  # TODO

        type_stack_under_args = type_stack[:-arg_count]
        type_stack_args = type_stack[-arg_count:]

        for arg_type, type_stack_arg in zip(arg_types, type_stack_args):
            if type(arg_type) != type(type_stack_arg) and not isinstance(
                arg_type, ArbitraryType
            ):
                raise NotImplementedError  # TODO

        return copy(type_stack_under_args) + return_types

    def integer_literal_type_check(
        self, node: AaaTreeNode, type_stack: List[BaseType]
    ) -> List[BaseType]:
        return type_stack + [Integer()]

    def string_literal_type_check(
        self, node: AaaTreeNode, type_stack: List[BaseType]
    ) -> List[BaseType]:
        return type_stack + [String()]

    def boolean_literal_type_check(
        self, node: AaaTreeNode, type_stack: List[BaseType]
    ) -> List[BaseType]:
        return type_stack + [Boolean()]

    def operator_type_check(
        self, node: AaaTreeNode, type_stack: List[BaseType]
    ) -> List[BaseType]:
        assert isinstance(node, Operator)
        signatures = OPERATOR_SIGNATURES[node.value]

        # TODO write loop
        assert len(signatures) == 1
        signature = signatures[0]

        return self.check_and_apply_signature(type_stack, signature[0], signature[1])

    def loop_type_check(
        self, node: AaaTreeNode, type_stack: List[BaseType]
    ) -> List[BaseType]:
        # TODO use copy on type_stack before checking children
        ...

    def identifier_type_check(
        self, node: AaaTreeNode, type_stack: List[BaseType]
    ) -> List[BaseType]:
        # TODO use copy on type_stack before checking children
        ...

    def branch_type_check(
        self, node: AaaTreeNode, type_stack: List[BaseType]
    ) -> List[BaseType]:
        # TODO use copy on type_stack before checking children
        ...

    def function_body_type_check(
        self, node: AaaTreeNode, type_stack: List[BaseType]
    ) -> List[BaseType]:
        # TODO use copy on type_stack before checking children
        ...

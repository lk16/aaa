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
OPERATOR_SIGNATURES: Dict[str, Tuple[List[BaseType], List[BaseType]]] = {
    "+": ...,  # TODO
    "-": ([Integer(), Integer()], [Integer()]),
    "*": ([Integer(), Integer()], [Integer()]),
    "/": ([Integer(), Integer()], [Integer()]),
    "%": ([Integer(), Integer()], [Integer()]),
    "and": ([Boolean(), Boolean()], [Boolean()]),
    "or": ([Boolean(), Boolean()], [Boolean()]),
    "not": ([Boolean()], [Boolean()]),
    "nop": ([], []),
    "=": ...,  # TODO
    ">": ([Integer(), Integer()], [Boolean()]),
    ">=": ([Integer(), Integer()], [Boolean()]),
    "<": ([Integer(), Integer()], [Boolean()]),
    "<=": ([Integer(), Integer()], [Boolean()]),
    "!=": ...,  # TODO
    "drop": ([ArbitraryType("a")], []),
    "dup": ([ArbitraryType("a")], [ArbitraryType("a"), ArbitraryType("a")]),
    "swap": (
        [ArbitraryType("a"), ArbitraryType("b")],
        [ArbitraryType("b"), ArbitraryType("a")],
    ),
    "over": (
        [ArbitraryType("a"), ArbitraryType("b")],
        [ArbitraryType("a"), ArbitraryType("b"), ArbitraryType("a")],
    ),
    "rot": ...,  # TODO
    "\\n": ([], []),
    ".": ...,  # TODO
    "substr": ...,  # TODO
    "strlen": ([String()], [Integer()]),
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
        raise NotImplementedError

    def integer_literal_type_check(
        self, node: AaaTreeNode, stack_types: List[BaseType]
    ) -> List[BaseType]:
        return stack_types + [Integer()]

    def string_literal_type_check(
        self, node: AaaTreeNode, stack_types: List[BaseType]
    ) -> List[BaseType]:
        return stack_types + [String()]

    def boolean_literal_type_check(
        self, node: AaaTreeNode, stack_types: List[BaseType]
    ) -> List[BaseType]:
        return stack_types + [Boolean()]

    def operator_type_check(
        self, node: AaaTreeNode, stack_types: List[BaseType]
    ) -> List[BaseType]:
        ...

    def loop_type_check(
        self, node: AaaTreeNode, stack_types: List[BaseType]
    ) -> List[BaseType]:
        ...

    def identifier_type_check(
        self, node: AaaTreeNode, stack_types: List[BaseType]
    ) -> List[BaseType]:
        ...

    def branch_type_check(
        self, node: AaaTreeNode, stack_types: List[BaseType]
    ) -> List[BaseType]:
        ...

    def function_body_type_check(
        self, node: AaaTreeNode, stack_types: List[BaseType]
    ) -> List[BaseType]:
        ...

from dataclasses import dataclass
from typing import Dict, List, Type

StackItem = int | bool | str


IDENTIFIER_TO_TYPE: Dict[str, Type[StackItem]] = {
    "bool": bool,
    "int": int,
    "str": str,
}


@dataclass
class SomeType:
    name: str


SignatureItem = Type[StackItem] | SomeType

TypeStack = List[SignatureItem]


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

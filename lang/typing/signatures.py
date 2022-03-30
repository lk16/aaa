from dataclasses import dataclass
from typing import Dict, List, Type

StackItem = int | bool | str


IDENTIFIER_TO_TYPE: Dict[str, Type[StackItem]] = {
    "bool": bool,
    "int": int,
    "str": str,
}


@dataclass
class PlaceholderType:
    name: str


SignatureItem = Type[StackItem] | PlaceholderType

TypeStack = List[SignatureItem]


@dataclass
class Signature:
    arg_types: List[SignatureItem]
    return_types: List[SignatureItem]


# TODO test that keys match instructions.py and grammar
OPERATOR_SIGNATURES: Dict[str, List[Signature]] = {
    "+": [
        Signature([int, int], [int]),
        Signature([str, str], [str]),
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
    ">": [Signature([int, int], [bool])],
    ">=": [Signature([int, int], [bool])],
    "<": [Signature([int, int], [bool])],
    "<=": [Signature([int, int], [bool])],
    "!=": [
        Signature([int, int], [bool]),
        Signature([str, str], [bool]),
    ],
    "drop": [Signature([PlaceholderType("a")], [])],
    "dup": [
        Signature([PlaceholderType("a")], [PlaceholderType("a"), PlaceholderType("a")])
    ],
    "swap": [
        Signature(
            [PlaceholderType("a"), PlaceholderType("b")],
            [PlaceholderType("b"), PlaceholderType("a")],
        )
    ],
    "over": [
        Signature(
            [PlaceholderType("a"), PlaceholderType("b")],
            [PlaceholderType("a"), PlaceholderType("b"), PlaceholderType("a")],
        )
    ],
    "rot": [
        Signature(
            [PlaceholderType("a"), PlaceholderType("b"), PlaceholderType("c")],
            [PlaceholderType("b"), PlaceholderType("c"), PlaceholderType("a")],
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
    "assert": [Signature([bool], [])],
}

from typing import Dict, List

from lang.typing.types import Bool, Int, PlaceholderType, Signature, Str

OPERATOR_SIGNATURES: Dict[str, List[Signature]] = {
    "+": [
        Signature([Int, Int], [Int]),
        Signature([Str, Str], [Str]),
    ],
    "-": [Signature([Int, Int], [Int])],
    "*": [Signature([Int, Int], [Int])],
    "/": [Signature([Int, Int], [Int])],
    "%": [Signature([Int, Int], [Int])],
    "and": [Signature([Bool, Bool], [Bool])],
    "or": [Signature([Bool, Bool], [Bool])],
    "not": [Signature([Bool], [Bool])],
    "nop": [Signature([], [])],
    "=": [
        Signature([Int, Int], [Bool]),
        Signature([Str, Str], [Str]),
    ],
    ">": [Signature([Int, Int], [Bool])],
    ">=": [Signature([Int, Int], [Bool])],
    "<": [Signature([Int, Int], [Bool])],
    "<=": [Signature([Int, Int], [Bool])],
    "!=": [
        Signature([Int, Int], [Bool]),
        Signature([Str, Str], [Bool]),
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
        Signature([Bool], []),
        Signature([Int], []),
        Signature([Str], []),
    ],
    "subStr": [Signature([Str, Int, Int], [Str])],
    "Strlen": [Signature([Str], [Int])],
    "assert": [Signature([Bool], [])],
}

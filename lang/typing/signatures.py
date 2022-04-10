from typing import Dict, List

from lang.typing.types import Bool, Int, Signature, Str, TypePlaceholder

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
    "drop": [Signature([TypePlaceholder("a")], [])],
    "dup": [
        Signature([TypePlaceholder("a")], [TypePlaceholder("a"), TypePlaceholder("a")])
    ],
    "swap": [
        Signature(
            [TypePlaceholder("a"), TypePlaceholder("b")],
            [TypePlaceholder("b"), TypePlaceholder("a")],
        )
    ],
    "over": [
        Signature(
            [TypePlaceholder("a"), TypePlaceholder("b")],
            [TypePlaceholder("a"), TypePlaceholder("b"), TypePlaceholder("a")],
        )
    ],
    "rot": [
        Signature(
            [TypePlaceholder("a"), TypePlaceholder("b"), TypePlaceholder("c")],
            [TypePlaceholder("b"), TypePlaceholder("c"), TypePlaceholder("a")],
        )
    ],
    "\\n": [Signature([], [])],
    ".": [
        Signature([Bool], []),
        Signature([Int], []),
        Signature([Str], []),
    ],
    "substr": [Signature([Str, Int, Int], [Str])],
    "strlen": [Signature([Str], [Int])],
    "assert": [Signature([Bool], [])],
}

from dataclasses import dataclass, replace
from enum import IntEnum
from typing import Callable, List, Optional, Set


@dataclass
class ParseTree:
    symbol_offset: int
    symbol_length: int
    symbol_type: Optional[IntEnum]
    children: List["ParseTree"]

    def size(self) -> int:
        return 1 + sum(child.size() for child in self.children)


def prune_parse_tree_zero_length(tree: ParseTree) -> Optional[ParseTree]:
    def condition(tree: ParseTree) -> bool:
        return tree.symbol_length > 0

    return prune_parse_tree(tree, condition)


def prune_by_symbol_types(
    tree: ParseTree, symbol_types: Set[IntEnum]
) -> Optional[ParseTree]:
    def condition(tree: ParseTree) -> bool:
        return tree.symbol_type is None or tree.symbol_type not in symbol_types

    return prune_parse_tree(tree, condition)


def prune_parse_tree(
    tree: ParseTree, condition: Callable[[ParseTree], bool]
) -> Optional[ParseTree]:
    if not condition(tree):
        return None

    pruned_children: List[ParseTree] = []

    for child in pruned_children:
        child_tree = prune_parse_tree(child, condition)
        if child_tree:
            pruned_children.append(child_tree)

    new_tree = replace(tree, children=pruned_children)
    return new_tree

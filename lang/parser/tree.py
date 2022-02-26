from dataclasses import dataclass, replace
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional, Set


@dataclass
class SymbolTree:
    symbol_offset: int
    symbol_length: int
    symbol_type: Optional[IntEnum]
    children: List["SymbolTree"]

    def size(self) -> int:
        return 1 + sum(child.size() for child in self.children)

    def dump(self, code: str) -> Dict[str, Any]:
        type_str = ""

        if self.symbol_type:
            type_str = self.symbol_type.name

        return {
            "value": self.value(code),
            "type": type_str,
            "children": [child.dump(code) for child in self.children],
        }

    def value(self, code: str) -> str:
        return code[self.symbol_offset : self.symbol_offset + self.symbol_length]


def prune_zero_length(tree: SymbolTree) -> Optional[SymbolTree]:
    def condition(tree: SymbolTree) -> bool:
        return tree.symbol_length > 0

    return prune_parse_tree(tree, condition)


def prune_by_symbol_types(
    tree: SymbolTree, symbol_types: Set[IntEnum]
) -> Optional[SymbolTree]:
    def condition(tree: SymbolTree) -> bool:
        return tree.symbol_type not in symbol_types

    return prune_parse_tree(tree, condition)


def prune_useless(tree: SymbolTree) -> Optional[SymbolTree]:
    def condition(tree: SymbolTree) -> bool:
        return not (tree.symbol_type is None and len(tree.children) == 0)

    return prune_parse_tree(tree, condition)


def prune_parse_tree(
    tree: SymbolTree, condition: Callable[[SymbolTree], bool]
) -> Optional[SymbolTree]:
    if not condition(tree):
        return None

    pruned_children: List[SymbolTree] = []

    for child in tree.children:
        child_tree = prune_parse_tree(child, condition)
        if child_tree:
            pruned_children.append(child_tree)

    new_tree = replace(tree, children=pruned_children)
    return new_tree

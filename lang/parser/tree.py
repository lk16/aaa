from dataclasses import dataclass
from enum import IntEnum
from typing import Callable, List, Optional, Set


@dataclass
class ParseTree:
    symbol_offset: int
    symbol_length: int
    symbol_type: Optional[IntEnum]
    children: List["ParseTree"]

    def count_nodes(self) -> int:
        return 1 + sum(child.count_nodes() for child in self.children)

    def prune(self, condition: Callable[["ParseTree"], bool]) -> "ParseTree":
        pruned_children = list(filter(condition, self.children))

        for i, child in enumerate(pruned_children):
            pruned_children[i] = child.prune(condition)

        return ParseTree(
            self.symbol_offset, self.symbol_length, self.symbol_type, pruned_children
        )

    def prune_zero_length_symbols(self) -> "ParseTree":
        return self.prune(lambda pt: pt.symbol_length > 0)

    def prune_by_symbol_types(self, symbol_types: Set[IntEnum]) -> "ParseTree":
        return self.prune(
            lambda pt: pt.symbol_type is None or pt.symbol_type not in symbol_types
        )

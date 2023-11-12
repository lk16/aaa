from __future__ import annotations

from copy import copy
from pathlib import Path
from typing import Any, Dict, List, Optional


class Choice:
    ...


class Position:
    def __init__(self, file: Path, line: int, column: int) -> None:
        self.file = file
        self.line = line
        self.column = column

    @classmethod
    def from_text(cls, file_name: str, offset: int, text: str) -> "Position":
        prefix = text[:offset]
        line = 1 + prefix.count("\n")
        column = offset - prefix.rfind("\n")
        return Position(Path(file_name), line, column)

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"

    def __hash__(self) -> int:
        return hash((self.file, self.line, self.column))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Position):
            return False

        return str(self) == str(other)

    def context(self, file_content: str) -> str:  # pragma: nocover
        line = file_content.split("\n")[self.line - 1]
        return line + "\n" + ((self.column - 1) * " ") + "^\n"

    def short_filename(self) -> str:  # pragma: nocover
        try:
            short = self.file.relative_to(Path.cwd())
        except ValueError:
            # It is possible the file is not in the subpath of cwd
            # We just print the absolute path then
            short = self.file

        return str(short)

    def __lt__(self, other: "Position") -> bool:
        return (self.file, self.line, self.column) < (
            other.file,
            other.line,
            other.column,
        )

    def __repr__(self) -> str:
        return str(self)


class Token:
    def __init__(self, value: str, type: str, position: Position) -> None:
        self.value = value
        self.type = type
        self.position = position

    def __len__(self) -> int:
        return len(self.value)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(type={repr(self.type)}, value={repr(self.value)})"
        )

    def as_json(self) -> Dict[str, Any]:
        return {"value": self.value, "type": self.type}


class InnerNode:
    def __init__(
        self, children: List["Token | InnerNode"], type: Optional[str] = None
    ) -> None:
        self.children: List[Token | InnerNode] = children
        self.type = type

    def __repr__(self) -> str:
        return f"{type(self).__name__}(type={repr(self.type)}, children={repr(self.children)})"

    def as_json(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "children": [child.as_json() for child in self.children],
        }

    def flatten(self) -> Node:
        if self.type is None:
            raise ValueError("Cannot call flatten on a node without a type!")

        children: List["Token | InnerNode"] = copy(self.children)

        while True:
            flattened_children: List["Token | InnerNode"] = []
            needs_more_flattening = False

            for child in children:
                if isinstance(child, Token):
                    flattened_children.append(child)
                elif child.type is None:
                    needs_more_flattening = True
                    for grand_child in child.children:
                        flattened_children.append(grand_child)
                else:
                    flattened_children.append(child)

            children = flattened_children

            if not needs_more_flattening:
                break

        flattened_node_children: List[Token | Node] = []

        for child in children:
            if isinstance(child, InnerNode):
                flattened_node_children.append(child.flatten())
            else:
                flattened_node_children.append(child)

        return Node(flattened_node_children, self.type)


class Node:
    def __init__(self, children: List["Token | Node"], type: str) -> None:
        self.children: List[Token | Node] = children
        self.type = type

    def __repr__(self) -> str:
        return f"{type(self).__name__}(type={repr(self.type)}, children={repr(self.children)})"

    def as_json(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "children": [child.as_json() for child in self.children],
        }

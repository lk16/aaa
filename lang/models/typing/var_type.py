from enum import IntEnum, auto
from typing import Any, Final, List

from lang.models import FunctionBodyItem


class RootType(IntEnum):
    BOOL = auto()
    INTEGER = auto()
    STRING = auto()
    VECTOR = auto()
    MAPPING = auto()
    STRUCT = auto()
    PLACEHOLDER = auto()

    def __repr__(self) -> str:  # pragma: nocover
        if self == RootType.BOOL:
            return "bool"
        elif self == RootType.INTEGER:
            return "int"
        elif self == RootType.STRING:
            return "str"
        elif self == RootType.VECTOR:
            return "vec"
        elif self == RootType.MAPPING:
            return "map"
        elif self == RootType.STRUCT:
            return "struct"
        elif self == RootType.PLACEHOLDER:
            return f"placeholder"
        else:
            assert False


class VariableType(FunctionBodyItem):
    root_type: RootType
    type_params: List["VariableType"]
    name: str = ""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        if self.root_type in [RootType.STRUCT, RootType.PLACEHOLDER]:
            assert self.name

    def __repr__(self) -> str:  # pragma: nocover
        if self.root_type == RootType.PLACEHOLDER:
            return f"*{self.name}"

        if self.root_type == RootType.STRUCT:
            formatted = self.name
        else:
            formatted = repr(self.root_type)

        if self.type_params:
            formatted += "["
            formatted += ", ".join(repr(type_param) for type_param in self.type_params)
            formatted += "]"

        return formatted

    def __str__(self) -> str:
        return repr(self)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, type(self)):  # pragma: nocover
            return False

        return self.root_type == o.root_type and self.type_params == o.type_params

    def is_placeholder(self) -> bool:
        return self.root_type == RootType.PLACEHOLDER


Bool: Final[VariableType] = VariableType(root_type=RootType.BOOL, type_params=[])
Int: Final[VariableType] = VariableType(root_type=RootType.INTEGER, type_params=[])
Str: Final[VariableType] = VariableType(root_type=RootType.STRING, type_params=[])

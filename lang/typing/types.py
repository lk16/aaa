from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Any, Final, List, Optional


class RootType(IntEnum):
    BOOL = auto()
    INT = auto()
    STR = auto()
    VEC = auto()
    MAP = auto()


class VariableType:
    def __init__(
        self, root_type: RootType, type_params: Optional[List[RootType]] = None
    ) -> None:
        self.root_type: Final[RootType] = root_type
        self.type_params: Final[List[RootType]] = type_params or []


Bool: Final[VariableType] = VariableType(RootType.BOOL)
Int: Final[VariableType] = VariableType(RootType.INT)
Str: Final[VariableType] = VariableType(RootType.STR)


TypeStack = List[VariableType]


class Variable:
    def __init__(
        self,
        root_type: RootType,
        value: Any,
        type_params: Optional[List[RootType]] = None,
    ) -> None:
        self.type: Final[VariableType] = VariableType(root_type, type_params)
        self.value = value
        self.check()

    def check(self) -> None:
        # TODO this is slow, remove when Variable is stable
        root_type = self.type.root_type
        type_params = self.type.type_params

        if root_type == RootType.BOOL:
            assert type(self.value) == bool

        elif root_type == RootType.INT:
            assert type(self.value) == int

        elif root_type == RootType.STR:
            assert type(self.value) == str

        elif root_type == RootType.VEC:
            assert type(self.value) == list
            assert len(type_params) == 1
            for item in self.value:
                assert item.type == type_params[0]
                item.check()

        elif root_type == RootType.MAP:
            assert type(self.value) == dict
            assert len(type_params) == 2
            for key, value in self.value.items():
                assert key.type == type_params[0]
                assert value.type == type_params[1]
                key.check()
                value.check()

        else:  # pragma: nocover
            assert False

    def __repr__(self) -> str:
        return repr(self.value)


@dataclass
class PlaceholderType:
    name: str


@dataclass
class Signature:
    arg_types: List[VariableType | PlaceholderType]
    return_types: List[VariableType | PlaceholderType]

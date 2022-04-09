from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Any, Final, List, Optional, Union

from lang.runtime.parse import TypeLiteral


class RootType(IntEnum):
    BOOL = auto()
    INTEGER = auto()
    STRING = auto()
    VECTOR = auto()
    MAPPING = auto()

    @classmethod
    def from_str(cls, name: str) -> "RootType":
        if name == "int":
            return RootType.INTEGER
        elif name == "bool":
            return RootType.BOOL
        elif name == "str":
            return RootType.STRING
        elif name == "vec":
            return RootType.VECTOR
        elif name == "map":
            return RootType.MAPPING
        else:  # pragma: nocover
            assert False


class VariableType:
    def __init__(
        self, root_type: RootType, type_params: Optional[List[RootType]] = None
    ) -> None:
        self.root_type: Final[RootType] = root_type
        self.type_params: Final[List[RootType]] = type_params or []

        if root_type == RootType.VECTOR:
            assert len(self.type_params) == 1
        elif root_type == RootType.MAPPING:
            assert len(self.type_params) == 2
        else:
            assert len(self.type_params) == 0

    @classmethod
    def from_type_literal(cls, type_literal: TypeLiteral) -> "VariableType":
        root_type = RootType.from_str(type_literal.type_name)

        type_params = [
            RootType.from_str(param.type_name) for param in type_literal.type_parameters
        ]

        return VariableType(root_type, type_params)

    def __repr__(self) -> str:
        if self.root_type == RootType.BOOL:
            return "bool"
        elif self.root_type == RootType.INTEGER:
            return "int"
        elif self.root_type == RootType.STRING:
            return "str"
        elif self.root_type == RootType.VECTOR:
            item = repr(self.type_params[0])
            return f"vec[{item}]"
        elif self.root_type == RootType.MAPPING:
            key = repr(self.type_params[0])
            value = repr(self.type_params[1])
            return f"map[{key}, {value}]"
        else:  # pragma: nocover
            assert False

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, type(self)):
            return False

        return self.root_type == o.root_type and self.type_params == o.type_params


Bool: Final[VariableType] = VariableType(RootType.BOOL)
Int: Final[VariableType] = VariableType(RootType.INTEGER)
Str: Final[VariableType] = VariableType(RootType.STRING)


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

        elif root_type == RootType.INTEGER:
            assert type(self.value) == int

        elif root_type == RootType.STRING:
            assert type(self.value) == str

        elif root_type == RootType.VECTOR:
            assert type(self.value) == list
            assert len(type_params) == 1
            for item in self.value:
                assert item.type == type_params[0]
                item.check()

        elif root_type == RootType.MAPPING:
            assert type(self.value) == dict
            assert len(type_params) == 2
            for key, value in self.value.items():
                assert key.type == type_params[0]
                assert value.type == type_params[1]
                key.check()
                value.check()

        else:  # pragma: nocover
            assert False

    def root_type(self) -> RootType:
        return self.type.root_type

    def has_root_type(self, root_type: RootType) -> bool:
        return self.root_type() == root_type

    def __repr__(self) -> str:
        if self.root_type() == RootType.BOOL:
            if self.value:
                return "true"
            else:
                return "false"

        return repr(self.value)

    def __str__(self) -> str:
        if self.root_type() == RootType.BOOL:
            if self.value:
                return "true"
            else:
                return "false"

        return str(self.value)


def int_var(value: int) -> Variable:
    return Variable(RootType.INTEGER, value)


def str_var(value: str) -> Variable:
    return Variable(RootType.STRING, value)


def bool_var(value: bool) -> Variable:
    return Variable(RootType.BOOL, value)


# TODO rename to TypePlaceholder
@dataclass
class PlaceholderType:
    name: str


SignatureItem = Union[VariableType, PlaceholderType]

TypeStack = List[SignatureItem]


@dataclass
class Signature:
    arg_types: List[SignatureItem]
    return_types: List[SignatureItem]

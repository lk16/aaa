from enum import IntEnum, auto
from typing import Any, Dict, Final, List, Optional, Union

from lang.models import AaaModel
from lang.models.parse import Function, ParsedTypePlaceholder, TypeLiteral


class RootType(IntEnum):
    BOOL = auto()
    INTEGER = auto()
    STRING = auto()
    VECTOR = auto()
    MAPPING = auto()
    STRUCT = auto()

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
        else:
            return RootType.STRUCT

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
        else:
            return "struct"


class VariableType:
    def __init__(
        self,
        root_type: RootType,
        type_params: Optional[List["SignatureItem"]] = None,
        struct_name: str = "",
    ) -> None:
        self.root_type: Final[RootType] = root_type
        self.type_params: Final[List[SignatureItem]] = type_params or []

        # TODO consider renaming struct_name to type_name
        # and remove RootType.__repr__() and its uses.

        if self.root_type == RootType.STRUCT:
            assert struct_name
            self.struct_name = struct_name
        else:
            self.struct_name = ""

        if root_type == RootType.VECTOR:
            assert len(self.type_params) == 1
        elif root_type == RootType.MAPPING:
            assert len(self.type_params) == 2
        else:
            assert len(self.type_params) == 0

    @classmethod
    def from_type_literal(cls, type_literal: TypeLiteral) -> "VariableType":
        root_type = RootType.from_str(type_literal.type_name)

        type_params: List[SignatureItem] = []

        for param in type_literal.type_parameters:
            if isinstance(param.type, TypeLiteral):
                type_params.append(VariableType.from_type_literal(param.type))
            elif isinstance(param.type, ParsedTypePlaceholder):
                type_params.append(TypePlaceholder(name=param.type.name))
            else:  # pragma: nocover
                assert False

        return VariableType(root_type, type_params, struct_name=type_literal.type_name)

    def __repr__(self) -> str:  # pragma: nocover
        if self.root_type == RootType.STRUCT:
            formatted = self.struct_name
        else:
            formatted = repr(self.root_type)

        if self.type_params:
            formatted += "["
            formatted += ", ".join(repr(type_param) for type_param in self.type_params)
            formatted += "]"

        return formatted

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, type(self)):  # pragma: nocover
            return False

        return self.root_type == o.root_type and self.type_params == o.type_params

    def get_variable_type_param(self, offset: int) -> "VariableType":
        """
        Prevents getting TypePlaceholder type_params
        """

        type_param = self.type_params[offset]
        assert isinstance(type_param, VariableType)
        return type_param


Bool: Final[VariableType] = VariableType(RootType.BOOL)
Int: Final[VariableType] = VariableType(RootType.INTEGER)
Str: Final[VariableType] = VariableType(RootType.STRING)


class Variable:
    def __init__(
        self,
        root_type: RootType,
        value: Any,
        type_params: Optional[List["SignatureItem"]] = None,
        struct_name: str = "",
    ) -> None:
        self.type: Final[VariableType] = VariableType(
            root_type, type_params, struct_name=struct_name
        )
        self.value = value
        self.check()

    @classmethod
    def zero_value(cls, type: VariableType) -> "Variable":
        zero_val: Any

        if type.root_type == RootType.BOOL:
            zero_val = False
        elif type.root_type == RootType.INTEGER:
            zero_val = 0
        elif type.root_type == RootType.STRING:
            zero_val = ""
        elif type.root_type == RootType.VECTOR:
            zero_val = []
        elif type.root_type in [RootType.MAPPING, RootType.STRUCT]:
            zero_val = {}
        else:  # pragma: nocover
            assert False

        return Variable(
            root_type=type.root_type, type_params=type.type_params, value=zero_val
        )

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
        elif root_type == RootType.STRUCT:
            assert type(self.value) == dict
            assert len(type_params) == 0
        else:  # pragma: nocover
            assert False

    def root_type(self) -> RootType:
        return self.type.root_type

    def has_root_type(self, root_type: RootType) -> bool:  # pragma: nocover
        return self.root_type() == root_type

    def __str__(self) -> str:
        root_type = self.root_type()

        if root_type in [RootType.INTEGER, RootType.STRING]:
            return str(self.value)

        elif root_type == RootType.BOOL:
            return str(self.value).lower()

        elif root_type == RootType.VECTOR:
            return "[" + ", ".join(repr(item) for item in self.value) + "]"

        elif root_type == RootType.MAPPING:
            return (
                "{"
                + ", ".join(
                    repr(key) + ": " + repr(value) for key, value in self.value.items()
                )
                + "}"
            )

        else:  # pragma: nocover
            assert False

    def __repr__(self) -> str:
        if self.root_type() == RootType.STRING:
            return '"' + str(self.value) + '"'

        return str(self)

    def __hash__(self) -> int:
        # NOTE: this will fail for VECTOR and MAPPING
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Variable):
            return False  # pragma: nocover

        return self.value == other.value  # type: ignore


def int_var(value: int) -> Variable:
    return Variable(RootType.INTEGER, value)


def str_var(value: str) -> Variable:
    return Variable(RootType.STRING, value)


def bool_var(value: bool) -> Variable:
    return Variable(RootType.BOOL, value)


def map_var(
    key_type: VariableType,
    value_type: VariableType,
    value: Dict[Variable, Variable],
) -> Variable:
    return Variable(
        root_type=RootType.MAPPING,
        type_params=[key_type, value_type],
        value=value,
    )


def list_var(
    item_type: VariableType,
    value: List[Variable],
) -> Variable:
    return Variable(
        root_type=RootType.VECTOR,
        type_params=[item_type],
        value=value,
    )


class TypePlaceholder(AaaModel):
    name: str

    def __repr__(self) -> str:  # pragma: nocover
        return f"*{self.name}"


SignatureItem = Union[VariableType, TypePlaceholder]

TypeStack = List[SignatureItem]


class Signature(AaaModel):
    class Config:
        arbitrary_types_allowed = True  # TODO make VariableType an AaaModel

    arg_types: List[SignatureItem]
    return_types: List[SignatureItem]

    @classmethod
    def from_function(cls, function: Function) -> "Signature":
        arg_types: List[SignatureItem] = []
        return_types: List[SignatureItem] = []
        # TODO reduce code duplication below

        for argument in function.arguments:
            type = argument.type.type  # TODO reduce indirections

            if isinstance(type, TypeLiteral):
                arg_types.append(VariableType.from_type_literal(type))
            elif isinstance(type, ParsedTypePlaceholder):
                arg_types.append(TypePlaceholder(name=type.name))
            else:  # pragma: nocover
                assert False

        for return_type in function.return_types:
            type = return_type.type  # TODO reduce indirections

            if isinstance(type, TypeLiteral):
                return_types.append(VariableType.from_type_literal(type))
            elif isinstance(type, ParsedTypePlaceholder):
                return_types.append(TypePlaceholder(name=type.name))
            else:  # pragma: nocover
                assert False

        return Signature(arg_types=arg_types, return_types=return_types)


class StructUpdateSignature:
    ...


class StructQuerySignature:
    ...

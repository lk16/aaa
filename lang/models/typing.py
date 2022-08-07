from enum import IntEnum, auto
from typing import Any, Dict, Final, List

from lang.models import AaaModel
from lang.models.parse import BuiltinFunction, Function, ParsedType


class RootType(IntEnum):
    BOOL = auto()
    INTEGER = auto()
    STRING = auto()
    VECTOR = auto()
    MAPPING = auto()
    STRUCT = auto()
    PLACEHOLDER = auto()

    @classmethod
    def from_parsed_type(cls, parsed_type: ParsedType) -> "RootType":
        if parsed_type.name == "int":
            return RootType.INTEGER
        elif parsed_type.name == "bool":
            return RootType.BOOL
        elif parsed_type.name == "str":
            return RootType.STRING
        elif parsed_type.name == "vec":
            return RootType.VECTOR
        elif parsed_type.name == "map":
            return RootType.MAPPING
        elif parsed_type.is_placeholder:
            return RootType.PLACEHOLDER
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
        elif self == RootType.STRUCT:
            return "struct"
        elif self == RootType.PLACEHOLDER:
            return f"placeholder"
        else:
            assert False


class VariableType(AaaModel):
    root_type: RootType
    type_params: List["VariableType"]
    name: str = ""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        if self.root_type in [RootType.STRUCT, RootType.PLACEHOLDER]:
            assert self.name

        if self.root_type == RootType.VECTOR:
            assert len(self.type_params) == 1
        elif self.root_type == RootType.MAPPING:
            assert len(self.type_params) == 2
        else:
            assert len(self.type_params) == 0

    @classmethod
    def from_parsed_type(cls, parsed_type: ParsedType) -> "VariableType":
        root_type = RootType.from_parsed_type(parsed_type)

        type_params: List[VariableType] = [
            VariableType.from_parsed_type(param) for param in parsed_type.parameters
        ]

        return VariableType(
            root_type=root_type,
            type_params=type_params,
            name=parsed_type.name,
        )

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


class Variable(AaaModel):
    type: VariableType
    value: Any

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
        elif type.root_type == RootType.PLACEHOLDER:
            # Can't get zero value of placeholder type.
            assert False
        else:  # pragma: nocover
            assert False

        return Variable(
            type=VariableType(root_type=type.root_type, type_params=type.type_params),
            value=zero_val,
        )

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

        elif root_type == RootType.STRUCT:
            return (
                f"<struct {self.type.name}>"
                + "{"
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
    return Variable(
        type=VariableType(root_type=RootType.INTEGER, type_params=[]), value=value
    )


def str_var(value: str) -> Variable:
    return Variable(
        type=VariableType(root_type=RootType.STRING, type_params=[]), value=value
    )


def bool_var(value: bool) -> Variable:
    return Variable(
        type=VariableType(root_type=RootType.BOOL, type_params=[]), value=value
    )


def map_var(
    key_type: VariableType,
    value_type: VariableType,
    value: Dict[Variable, Variable],
) -> Variable:
    return Variable(
        type=VariableType(
            root_type=RootType.MAPPING, type_params=[key_type, value_type]
        ),
        value=value,
    )


def list_var(
    item_type: VariableType,
    value: List[Variable],
) -> Variable:
    return Variable(
        type=VariableType(root_type=RootType.VECTOR, type_params=[item_type]),
        value=value,
    )


class Signature(AaaModel):
    arg_types: List[VariableType]
    return_types: List[VariableType]

    @classmethod
    def from_function(cls, function: Function) -> "Signature":
        return Signature(
            arg_types=[
                VariableType.from_parsed_type(argument.type)
                for argument in function.arguments
            ],
            return_types=[
                VariableType.from_parsed_type(return_type)
                for return_type in function.return_types
            ],
        )

    @classmethod
    def from_builtin_function(cls, builtin_function: BuiltinFunction) -> "Signature":
        return Signature(
            arg_types=[
                VariableType.from_parsed_type(argument)
                for argument in builtin_function.arguments
            ],
            return_types=[
                VariableType.from_parsed_type(return_type)
                for return_type in builtin_function.return_types
            ],
        )


class StructUpdateSignature:
    ...


class StructQuerySignature:
    ...


VariableType.update_forward_refs()


Bool: Final[VariableType] = VariableType(root_type=RootType.BOOL, type_params=[])
Int: Final[VariableType] = VariableType(root_type=RootType.INTEGER, type_params=[])
Str: Final[VariableType] = VariableType(root_type=RootType.STRING, type_params=[])

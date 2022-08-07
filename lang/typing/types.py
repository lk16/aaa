from enum import IntEnum, auto
from typing import Any, Dict, Final, List

from lang.models import AaaModel
from lang.models.parse import Function, ParsedType


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
    def from_type_literal(cls, parsed_type: ParsedType) -> "VariableType":
        # TODO make this work for PLACEHOLDER root_type as well

        root_type = RootType.from_parsed_type(parsed_type)

        type_params: List[VariableType] = []

        for param in parsed_type.parameters:
            if not parsed_type.is_placeholder:  # TODO swap if/else
                type_params.append(VariableType.from_type_literal(param))
            else:
                type_params.append(
                    VariableType(
                        root_type=RootType.PLACEHOLDER,
                        type_params=[],
                        name=param.name,
                    )
                )

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

    def get_variable_type_param(self, offset: int) -> "VariableType":
        """
        Prevents getting TypePlaceholder type_params
        """

        type_param = self.type_params[offset]
        assert isinstance(type_param, VariableType)
        return type_param


class Variable(AaaModel):

    type: VariableType
    value: Any

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
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
        elif type.root_type == RootType.PLACEHOLDER:
            # Can't get zero value of placeholder type.
            assert False
        else:  # pragma: nocover
            assert False

        return Variable(
            type=VariableType(root_type=type.root_type, type_params=type.type_params),
            value=zero_val,
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
        arg_types: List[VariableType] = []
        return_types: List[VariableType] = []
        # TODO reduce code duplication below

        for argument in function.arguments:
            if not argument.type.is_placeholder:  # TODO swap if/else
                arg_types.append(VariableType.from_type_literal(argument.type))
            else:
                arg_types.append(
                    VariableType(
                        root_type=RootType.PLACEHOLDER,
                        type_params=[],
                        name=argument.type.name,
                    )
                )

        for return_type in function.return_types:
            if not return_type.is_placeholder:  # TODO swap if/else
                return_types.append(VariableType.from_type_literal(return_type))
            else:
                return_types.append(
                    VariableType(
                        root_type=RootType.PLACEHOLDER,
                        type_params=[],
                        name=return_type.name,
                    )
                )

        return Signature(arg_types=arg_types, return_types=return_types)


class StructUpdateSignature:
    ...


class StructQuerySignature:
    ...


VariableType.update_forward_refs()


Bool: Final[VariableType] = VariableType(root_type=RootType.BOOL, type_params=[])
Int: Final[VariableType] = VariableType(root_type=RootType.INTEGER, type_params=[])
Str: Final[VariableType] = VariableType(root_type=RootType.STRING, type_params=[])

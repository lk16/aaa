from typing import Any, Dict, List

from lang.models import AaaModel
from lang.models.typing.var_type import Bool, Int, RootType, Str, VariableType


class Variable(AaaModel):
    type: VariableType
    value: Any

    # TODO make member function of VariableType
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
        elif type.root_type == RootType.PLACEHOLDER:  # pragma: nocover
            # Can't get zero value of placeholder type.
            assert False
        else:  # pragma: nocover
            assert False

        return Variable(type=type, value=zero_val)

    def root_type(self) -> RootType:
        return self.type.root_type

    def has_root_type(self, root_type: RootType) -> bool:  # pragma: nocover
        return self.root_type() == root_type

    def __str__(self) -> str:  # pragma: nocover
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
    return Variable(type=Int, value=value)


def str_var(value: str) -> Variable:
    return Variable(type=Str, value=value)


def bool_var(value: bool) -> Variable:
    return Variable(type=Bool, value=value)


def vec_var(
    item_type: VariableType,
    value: List[Variable],
) -> Variable:
    return Variable(
        type=VariableType(root_type=RootType.VECTOR, type_params=[item_type]),
        value=value,
    )


def map_var(
    key_type: VariableType,
    value_type: VariableType,
    value: Dict[Variable, Variable],
) -> Variable:
    return Variable(
        type=VariableType(
            name="map", root_type=RootType.MAPPING, type_params=[key_type, value_type]
        ),
        value=value,
    )

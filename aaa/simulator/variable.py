from typing import Any

from aaa import AaaModel
from aaa.cross_referencer.models import Type


class Variable(AaaModel):
    def __init__(self, type: Type, value: Any):
        self.type = type
        self.value = value

    def __str__(self) -> str:  # pragma: nocover
        return (
            f"<struct {self.type.name}>"
            + "{"
            + ", ".join(
                repr(key) + ": " + repr(value) for key, value in self.value.items()
            )
            + "}"
        )

    def __repr__(self) -> str:
        return str(self)

    def __hash__(self) -> int:
        # NOTE: this will fail for VECTOR and MAPPING
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Variable)
            and self.type == self.type
            and self.value == other.value
        )  # type: ignore


class IntVar(Variable):
    def __init__(self, type: Type, value: int):
        assert type.name == "int"
        super().__init__(type=type, value=value)


class StrVar(Variable):
    def __init__(self, type: Type, value: str):
        assert type.name == "str"
        super().__init__(type=type, value=value)


class BoolVar(Variable):
    def __init__(self, type: Type, value: bool):
        assert type.name == "bool"
        super().__init__(type=type, value=value)


class VecVar(Variable):
    def __init__(self, type: Type, item_type: Type):
        assert type.name == "vec"
        self.item_type = item_type
        super().__init__(type=type, value=[])

    def __str__(self) -> str:  # pragma: nocover
        return repr(self.value)


class MapVar(Variable):
    def __init__(self, type: Type, key_type: Type, value_type: Type):
        assert type.name == "map"
        self.key_type = key_type
        self.value_type = value_type
        super().__init__(type=type, value={})

    def __str__(self) -> str:  # pragma: nocover
        return repr(self.value)

from typing import Any, Dict, List

from aaa import AaaModel


class Variable(AaaModel):
    def __init__(self, value: Any):
        self.value = value

    def __str__(self) -> str:  # pragma: nocover
        return (
            f"<struct>"
            + "{"
            + ", ".join(
                repr(key) + ": " + repr(value) for key, value in self.value.items()
            )
            + "}"
        )

    def __repr__(self) -> str:
        return str(self)

    def __hash__(self) -> int:
        # NOTE: this will fail for list and dict-style values
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Variable) and self.value == other.value


class IntVar(Variable):
    def __init__(self, value: int) -> None:
        super().__init__(value=value)

    def __str__(self) -> str:
        return str(self.value)


class StrVar(Variable):
    def __init__(self, value: str) -> None:
        super().__init__(value=value)

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        escaped = (
            self.value.replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("'", "\\'")
            .replace('"', '\\"')
        )
        return f'"{escaped}"'


class BoolVar(Variable):
    def __init__(self, value: bool) -> None:
        super().__init__(value=value)

    def __str__(self) -> str:
        return str(self.value).lower()


class VecVar(Variable):
    def __init__(self, value: List[Any]) -> None:
        super().__init__(value=value)

    def __str__(self) -> str:  # pragma: nocover
        return repr(self.value)


class MapVar(Variable):
    def __init__(self, value: Dict[Any, Any]) -> None:
        super().__init__(value=value)

    def __str__(self) -> str:  # pragma: nocover
        return repr(self)

    def __repr__(self) -> str:
        return (
            "{"
            + ", ".join(
                f"{repr(key)}: {repr(value)}" for (key, value) in self.value.items()
            )
            + "}"
        )

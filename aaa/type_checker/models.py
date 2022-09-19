from typing import TYPE_CHECKING, List

from aaa import AaaModel
from aaa.cross_referencer.models import VariableType

if TYPE_CHECKING:
    from aaa.type_checker.exceptions import TypeCheckerException


class AaaTypeCheckerModel(AaaModel):
    ...


class Signature(AaaTypeCheckerModel):
    def __init__(
        self, *, arguments: List[VariableType], return_types: List[VariableType]
    ) -> None:
        self.arguments = arguments
        self.return_types = return_types


class StructQuerySignature(AaaTypeCheckerModel):
    ...


class StructUpdateSignature(AaaTypeCheckerModel):
    ...


class TypeCheckerOutput(AaaModel):
    def __init__(
        self,
        *,
        exceptions: List["TypeCheckerException"],
    ) -> None:
        self.exceptions = exceptions

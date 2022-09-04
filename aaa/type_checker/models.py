from typing import List

from aaa import AaaModel
from aaa.cross_referencer.models import VariableType


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

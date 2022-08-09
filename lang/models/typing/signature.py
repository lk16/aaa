from typing import List

from lang.models import AaaModel
from lang.models.typing.var_type import VariableType


class Signature(AaaModel):
    arg_types: List[VariableType]
    return_types: List[VariableType]


class StructUpdateSignature:
    ...


class StructQuerySignature:
    ...

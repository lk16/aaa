from typing import List

from lang.models import AaaModel
from lang.models.parse import BuiltinFunction
from lang.models.typing.var_type import VariableType


class Signature(AaaModel):
    arg_types: List[VariableType]
    return_types: List[VariableType]

    @classmethod
    def from_builtin_function(cls, builtin_function: BuiltinFunction) -> "Signature":
        return Signature(
            arg_types=builtin_function.arguments,
            return_types=builtin_function.return_types,
        )


class StructUpdateSignature:
    ...


class StructQuerySignature:
    ...

from basil.models import Position

from aaa import AaaModel
from aaa.cross_referencer.models import FunctionPointer, Never, VariableType


class TypeCheckerOutput(AaaModel):
    def __init__(
        self,
        foreach_loop_stacks: dict[
            Position, list[VariableType | FunctionPointer] | Never
        ],
    ) -> None:
        self.position_stacks = foreach_loop_stacks

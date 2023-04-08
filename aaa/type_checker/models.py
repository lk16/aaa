from typing import Dict, List

from aaa import AaaModel, Position
from aaa.cross_referencer.models import Never, VariableType


class TypeCheckerOutput(AaaModel):
    def __init__(
        self, foreach_loop_stacks: Dict[Position, List[VariableType] | Never]
    ) -> None:
        self.position_stacks = foreach_loop_stacks

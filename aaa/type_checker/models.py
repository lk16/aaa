from typing import Dict, List

from aaa import AaaModel, Position
from aaa.cross_referencer.models import VariableType


class TypeCheckerOutput(AaaModel):
    def __init__(self, foreach_loop_stacks: Dict[Position, List[VariableType]]) -> None:
        self.foreach_loop_stacks = foreach_loop_stacks

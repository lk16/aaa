from pathlib import Path
from typing import Dict

from aaa import AaaModel
from aaa.cross_referencer.models import Function
from aaa.simulator.variable import Variable


class CallStackItem(AaaModel):
    def __init__(
        self,
        function: Function,
        source_file: Path,
        instruction_pointer: int,
        argument_values: Dict[str, Variable],
    ) -> None:
        self.function = function
        self.source_file = source_file
        self.instruction_pointer = instruction_pointer
        self.argument_values = argument_values

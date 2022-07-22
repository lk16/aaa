from pathlib import Path
from typing import Dict

from lang.models import AaaModel
from lang.models.parse import Function
from lang.typing.types import Variable


class CallStackItem(AaaModel):
    class Config:
        arbitrary_types_allowed = True  # TODO fix

    function: Function
    source_file: Path
    instruction_pointer: int
    argument_values: Dict[str, Variable]

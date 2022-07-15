from pathlib import Path
from typing import Dict

from lang.models import AaaModel
from lang.typing.types import Variable


class CallStackItem(AaaModel):
    class Config:
        arbitrary_types_allowed = True  # TODO fix

    func_name: str
    source_file: Path
    instruction_pointer: int
    argument_values: Dict[str, Variable]

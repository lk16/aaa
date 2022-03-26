import inspect
import sys

from lang.instruction_types import Instruction
from lang.simulator import Simulator


def test_program_implements_all_instructions() -> None:
    instruction_types = {
        obj
        for _, obj in inspect.getmembers(sys.modules["lang.instruction_types"])
        if inspect.isclass(obj) and obj is not Instruction
    }

    implemented_instructions = set(Simulator({}).instruction_funcs.keys())
    assert instruction_types == implemented_instructions

import inspect
import sys

from lang.instructions.types import Instruction
from lang.runtime.program import Program
from lang.runtime.simulator import Simulator


def test_program_implements_all_instructions() -> None:
    instruction_types = {
        obj
        for _, obj in inspect.getmembers(sys.modules["lang.instructions.types"])
        if inspect.isclass(obj)
        and issubclass(obj, Instruction)
        and obj is not Instruction
    }

    simulator = Simulator(Program.without_file("fn main { nop }"))
    implemented_instructions = set(simulator.instruction_funcs.keys())
    assert instruction_types == implemented_instructions

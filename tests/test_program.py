import inspect
import sys
from pathlib import Path

from aaa.instruction_generator.models import Instruction, InstructionGeneratorOutput
from aaa.run import Runner
from aaa.simulator.simulator import Simulator


def test_program_load_builtins_ok() -> None:
    runner = Runner.without_file("fn main { nop }")
    assert runner.run() == 0


def test_program_implements_all_instructions() -> None:
    instruction_types = {
        obj
        for _, obj in inspect.getmembers(
            sys.modules["aaa.instruction_generator.models"]
        )
        if inspect.isclass(obj)
        and issubclass(obj, Instruction)
        and obj is not Instruction
    }

    simulator = Simulator(InstructionGeneratorOutput({}, {}, {}, Path("."), Path(".")))
    implemented_instructions = set(simulator.instruction_funcs.keys())
    assert instruction_types == implemented_instructions

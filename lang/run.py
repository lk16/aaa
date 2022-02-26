from typing import List

from lang.instructions import Instruction
from lang.program import Program


def run(program: Program, verbose: bool = False) -> None:
    program.run(verbose=verbose)


def run_as_main(instructions: List[Instruction], verbose: bool = False) -> None:
    # TODO
    raise NotImplementedError

from typing import List

from lang.program import Program
from lang.types import Function, Operation


def run(program: Program, verbose: bool = False) -> None:
    program.run(verbose=verbose)


def run_as_main(operations: List[Operation], verbose: bool = False) -> None:
    functions = {"main": Function("main", 0, operations)}

    Program(functions).run(verbose=verbose)

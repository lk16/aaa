from typing import List

from lang.operations import Function, Operation
from lang.program import Program


def run(program: Program, verbose: bool = False) -> None:
    program.run(verbose=verbose)


def run_as_main(operations: List[Operation], verbose: bool = False) -> None:
    functions = {"main": Function("main", 0, operations)}

    Program(functions).run(verbose=verbose)

import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir
from typing import Sequence

from aaa import AaaException
from aaa.cross_referencer.cross_referencer import CrossReferencer
from aaa.instruction_generator.instruction_generator import InstructionGenerator
from aaa.parser.parser import Parser
from aaa.simulator.exceptions import AaaRuntimeException
from aaa.simulator.simulator import Simulator
from aaa.type_checker.type_checker import TypeChecker


class Runner:
    def __init__(self, entrypoint: Path) -> None:
        self.entrypoint = entrypoint
        self.exceptions: Sequence[AaaException] = []

    @staticmethod
    def without_file(code: str) -> "Runner":
        temp_file = NamedTemporaryFile(delete=False)
        file = Path(gettempdir()) / temp_file.name
        file.write_text(code)
        return Runner(file)

    def _print_exceptions(self) -> None:
        for exception in self.exceptions:
            print(str(exception), end="", file=sys.stderr)
            print()

        print(f"Found {len(self.exceptions)} errors.", file=sys.stderr)

    def run(self) -> int:
        try:
            stdlib_path = Path(os.environ["AAA_STDLIB_PATH"]) / "builtins.aaa"
        except KeyError:
            print("Environment variable AAA_STDLIB_PATH is not set.")
            print("Cannot find standard library!")
            return 1

        parser_output = Parser(self.entrypoint, stdlib_path).run()
        self.exceptions = parser_output.exceptions

        if self.exceptions:
            self._print_exceptions()
            return 1

        cross_referencer_output = CrossReferencer(parser_output).run()
        self.exceptions = cross_referencer_output.exceptions

        if self.exceptions:
            self._print_exceptions()
            return 1

        type_checker_output = TypeChecker(cross_referencer_output).run()

        self.exceptions = type_checker_output.exceptions

        if self.exceptions:
            self._print_exceptions()
            return 1

        instruction_generator = InstructionGenerator(cross_referencer_output)
        instruction_generator_output = instruction_generator.run()

        simulator = Simulator(instruction_generator_output, False)

        try:
            simulator.run(True)
        except AaaRuntimeException as e:
            print(f"Runtime exception {type(e).__name__}", file=sys.stderr)
            self.exceptions = [e]
            return 1

        return 0

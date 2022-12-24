import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir
from typing import Dict, Optional, Sequence

from aaa import AaaException, AaaRunnerException
from aaa.cross_referencer.cross_referencer import CrossReferencer
from aaa.instruction_generator.instruction_generator import InstructionGenerator
from aaa.parser.models import ParsedFile
from aaa.parser.parser import Parser
from aaa.simulator.exceptions import AaaRuntimeException
from aaa.simulator.simulator import Simulator
from aaa.transpiler.transpiler import Transpiler
from aaa.type_checker.type_checker import TypeChecker


class Runner:
    def __init__(
        self,
        entrypoint: Path,
        parsed_files: Optional[Dict[Path, ParsedFile]],
        verbose: bool,
    ) -> None:
        self.entrypoint = entrypoint
        self.exceptions: Sequence[AaaException] = []
        self.parsed_files = parsed_files or {}
        self.verbose = verbose

    @staticmethod
    def without_file(
        code: str, parsed_files: Optional[Dict[Path, ParsedFile]], verbose: bool
    ) -> "Runner":
        temp_file = NamedTemporaryFile(delete=False)
        file = Path(gettempdir()) / temp_file.name
        file.write_text(code)
        return Runner(file, parsed_files, verbose)

    def _print_exceptions(self, runner_exception: AaaRunnerException) -> None:
        for exception in runner_exception.exceptions:
            print(str(exception), file=sys.stderr)

        print(f"Found {len(runner_exception.exceptions)} error(s).", file=sys.stderr)

    def _get_stdlib_path(self) -> Path:
        try:
            stdlib_folder = os.environ["AAA_STDLIB_PATH"]
        except KeyError as e:
            raise AaaRuntimeException(
                "Environment variable AAA_STDLIB_PATH is not set.\n"
                + "Cannot find standard library!"
            ) from e

        return Path(stdlib_folder) / "builtins.aaa"

    def run(self) -> int:
        try:
            stdlib_path = self._get_stdlib_path()

            parser = Parser(
                self.entrypoint, stdlib_path, self.parsed_files, self.verbose
            )
            parser_output = parser.run()

            cross_referencer_output = CrossReferencer(parser_output, self.verbose).run()

            TypeChecker(cross_referencer_output, self.verbose).run()

            instruction_gen = InstructionGenerator(
                cross_referencer_output, self.verbose
            )
            instruction_gen_output = instruction_gen.run()

            Simulator(instruction_gen_output, self.verbose).run()
        except AaaRunnerException as e:
            self.exceptions = e.exceptions
            self._print_exceptions(e)
            return 1
        except AaaException as e:
            self.exceptions = [e]
            self._print_exceptions(AaaRunnerException([e]))
            return 1

        return 0

    def transpile(self, output_file: Path, compile: bool, run: bool) -> int:
        try:
            stdlib_path = self._get_stdlib_path()

            parser = Parser(
                self.entrypoint, stdlib_path, self.parsed_files, self.verbose
            )
            parser_output = parser.run()

            cross_referencer_output = CrossReferencer(parser_output, self.verbose).run()

            TypeChecker(cross_referencer_output, self.verbose).run()

            transpiler = Transpiler(cross_referencer_output, output_file, self.verbose)
            transpiler.run(compile, run)

        except AaaRunnerException as e:
            self.exceptions = e.exceptions
            self._print_exceptions(e)
            return 1
        except AaaException as e:
            self.exceptions = [e]
            self._print_exceptions(AaaRunnerException([e]))
            return 1

        return 0

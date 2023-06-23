import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir
from typing import Dict, Optional, Sequence

from aaa import AaaException, AaaRunnerException, AaaRuntimeException
from aaa.cross_referencer.cross_referencer import CrossReferencer
from aaa.parser.models import ParsedFile
from aaa.parser.parser import Parser
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
        self.generated_binary_file: Path

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

    def run(self, compile: bool, binary: Optional[str], run: bool) -> int:
        if binary is not None and not compile:
            print(
                "Specifying binary path without compiling does not make sense.",
                file=sys.stderr,
            )
            exit(1)

        if run and not compile:
            print("Can't run binary without (re-)compiling!", file=sys.stderr)
            exit(1)

        generated_binary_file: Optional[Path] = None
        if binary:
            generated_binary_file = Path(binary).resolve()

        try:
            stdlib_path = self._get_stdlib_path()

            parser = Parser(
                self.entrypoint, stdlib_path, self.parsed_files, self.verbose
            )
            parser_output = parser.run()

            cross_referencer_output = CrossReferencer(parser_output, self.verbose).run()

            type_checker = TypeChecker(cross_referencer_output, self.verbose)
            type_checker_output = type_checker.run()

            transpiler = Transpiler(
                cross_referencer_output,
                type_checker_output,
                generated_binary_file,
                self.verbose,
            )

            self.generated_binary_file = transpiler.generated_binary_file

            return transpiler.run(compile, run)

        except AaaRunnerException as e:
            self.exceptions = e.exceptions
            self._print_exceptions(e)
            return 1
        except AaaException as e:
            self.exceptions = [e]
            self._print_exceptions(AaaRunnerException([e]))
            return 1

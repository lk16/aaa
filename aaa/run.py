import os
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir
from typing import Dict, List, Optional, Sequence

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

    def run(
        self,
        compile: bool,
        custom_binary_path: Optional[Path],
        run: bool,
        args: List[str],
    ) -> int:
        if custom_binary_path is not None and not compile:
            print(
                "Specifying binary path without compiling does not make sense.",
                file=sys.stderr,
            )
            exit(1)

        if run and not compile:
            print("Can't run binary without (re-)compiling!", file=sys.stderr)
            exit(1)

        entrypoint_hash = sha256(bytes(self.entrypoint)).hexdigest()[:16]
        transpiler_root = Path("/tmp/aaa/transpiled") / entrypoint_hash

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
                transpiler_root,
                self.verbose,
            )

            transpiler.run()

        except AaaRunnerException as e:
            self.exceptions = e.exceptions
            self._print_exceptions(e)
            return 1
        except AaaException as e:
            self.exceptions = [e]
            self._print_exceptions(AaaRunnerException([e]))
            return 1

        if compile:  # pragma: nocover
            cargo_toml = (transpiler_root / "Cargo.toml").resolve()
            command = ["cargo", "build", "--quiet", "--manifest-path", str(cargo_toml)]
            exit_code = subprocess.run(command).returncode

            if exit_code != 0:
                return exit_code

            binary_file = transpiler_root / "target/debug/aaa-stdlib-user"
            if custom_binary_path:
                binary_file = binary_file.rename(custom_binary_path)

            if run:  # pragma: nocover
                command = [str(binary_file)] + args
                return subprocess.run(command).returncode

        return 0

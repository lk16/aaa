import os
import subprocess
import sys
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any, Dict, List, Optional, Sequence, Tuple

from aaa import AaaException, create_output_folder, create_test_output_folder
from aaa.cross_referencer.cross_referencer import CrossReferencer
from aaa.parser.models import ParsedFile
from aaa.parser.parser import Parser
from aaa.runner.exceptions import (
    AaaEnvironmentError,
    AaaTranslationException,
    ExcecutableDidNotRun,
    RustCompilerError,
)
from aaa.transpiler.transpiler import Transpiler
from aaa.type_checker.type_checker import TypeChecker


class Runner:
    def __init__(self, entrypoint: str | Path) -> None:
        self.entrypoint = Path(entrypoint).resolve()
        self.verbose = False
        self.exceptions: Sequence[AaaException] = []
        self.parsed_files: Dict[Path, ParsedFile] = {}
        self.verbose = False

    @staticmethod
    def without_file(code: str) -> "Runner":
        entrypoint = create_test_output_folder() / "main.aaa"
        entrypoint.write_text(code)
        return Runner(entrypoint)

    def add_parsed_files(self, parsed_files: Dict[Path, ParsedFile]) -> None:
        self.parsed_files.update(parsed_files)

    def set_verbose(self, verbose: bool) -> None:
        self.verbose = verbose

    def _print_exceptions(self, runner_exception: AaaTranslationException) -> None:
        for exception in runner_exception.exceptions:
            print(str(exception), file=sys.stderr)

        print(f"Found {len(runner_exception.exceptions)} error(s).", file=sys.stderr)

    def _get_stdlib_path(self) -> Path:
        try:
            stdlib_folder = os.environ["AAA_STDLIB_PATH"]
        except KeyError as e:
            raise AaaEnvironmentError(
                "Environment variable AAA_STDLIB_PATH is not set.\n"
                + "Cannot find standard library!"
            ) from e

        return Path(stdlib_folder) / "builtins.aaa"

    def run(
        self,
        *,
        compile: bool,
        binary_path: Optional[Path],
        run: bool,
        args: List[str],
        **run_kwargs: Any,
    ) -> CompletedProcess[bytes]:
        transpiled = self.transpile()

        if not compile:
            raise ExcecutableDidNotRun

        compiled = transpiled.compile(binary_path, self.verbose)

        if not run:
            raise ExcecutableDidNotRun

        return compiled.execute(args, **run_kwargs)

    def transpile(self) -> "Transpiled":
        transpiler_root = create_output_folder()

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

        except AaaTranslationException as e:
            self.exceptions = e.exceptions
            self._print_exceptions(e)
            raise e

        except RustCompilerError as e:
            raise e

        except AaaException as e:
            self.exceptions = [e]
            self._print_exceptions(AaaTranslationException([e]))
            raise e

        return Transpiled(transpiler_root)


def compile_run(
    entrypoint: Path, binary_path: Optional[Path] = None, **run_kwargs: Any
) -> Tuple[str, str, int]:
    completed_process = Runner(entrypoint).run(
        compile=True,
        binary_path=binary_path,
        run=True,
        args=[],
        capture_output=True,
        **run_kwargs,
    )

    return (
        completed_process.stdout.decode("utf-8"),
        completed_process.stderr.decode("utf-8"),
        completed_process.returncode,
    )


class Transpiled:
    def __init__(self, transpiler_root: Path) -> None:
        self.transpiler_root = transpiler_root

    def compile(
        self, binary_path: Optional[Path] = None, verbose: bool = False
    ) -> "Compiled":
        # Use shared target dir between executables,
        # because every Aaa compilation would otherwise take 120 MB disk, due to Rust dependencies.
        cargo_shared_target_dir = create_output_folder("") / "shared_target"
        cargo_shared_target_dir.mkdir(exist_ok=True, parents=True)

        compiler_env = os.environ.copy()
        compiler_env["CARGO_TARGET_DIR"] = str(cargo_shared_target_dir)

        cargo_toml = (self.transpiler_root / "Cargo.toml").resolve()
        command = ["cargo", "build", "--quiet", "--manifest-path", str(cargo_toml)]

        completed_process = subprocess.run(
            command, env=compiler_env, capture_output=True
        )

        exit_code = completed_process.returncode

        if verbose:
            print(completed_process.stdout.decode("utf-8"))
            print(completed_process.stderr.decode("utf-8"), file=sys.stderr)

        if exit_code != 0:
            raise RustCompilerError()

        default_binary_path = cargo_shared_target_dir / "debug/aaa-stdlib-user"
        if binary_path:
            binary_path = default_binary_path.rename(binary_path)

        return Compiled(binary_path or default_binary_path)


class Compiled:
    def __init__(self, binary_file: Path) -> None:
        self.binary_file = binary_file

    def execute(self, args: List[str], **run_kwargs: Any) -> CompletedProcess[bytes]:
        command = [str(self.binary_file)] + args
        return subprocess.run(command, **run_kwargs)

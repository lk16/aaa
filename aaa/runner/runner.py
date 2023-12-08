import os
import subprocess
import sys
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any, Dict, List, Optional, Sequence, Tuple

from aaa import AaaException, create_output_folder
from aaa.cross_referencer.cross_referencer import CrossReferencer
from aaa.parser.models import SourceFile
from aaa.parser.parser import AaaParser
from aaa.runner.exceptions import (
    AaaTranslationException,
    ExcecutableDidNotRun,
    RustCompilerError,
)
from aaa.transpiler.transpiler import Transpiler
from aaa.type_checker.type_checker import TypeChecker

CARGO_TOML_TEMPLATE = """
[package]
name = "aaa-stdlib-user"
version = "0.1.0"
edition = "2021"
# See more keys and their definitions at https://doc.rust-lang.org/cargo/reference/manifest.html

[dependencies]
aaa-stdlib = {{ version = "0.1.0", path = "{stdlib_impl_path}" }}
regex = "1.8.4"
"""

RUNNER_FILE_DICT_ROOT_PATH = Path("/aaa/runner/root")  # This file should not exist


class Runner:
    def __init__(
        self, entrypoint: Path, file_dict: Optional[Dict[Path, str]] = None
    ) -> None:
        assert not RUNNER_FILE_DICT_ROOT_PATH.exists()

        self.file_dict: Dict[Path, str] = {}
        if file_dict:
            assert not entrypoint.is_absolute()
            assert entrypoint in file_dict.keys()

            for file, code in file_dict.items():
                assert not file.is_absolute()
                self.file_dict[RUNNER_FILE_DICT_ROOT_PATH / file] = code

            self.entrypoint = RUNNER_FILE_DICT_ROOT_PATH / entrypoint
        else:
            self.entrypoint = Path(entrypoint).resolve()

        self.verbose = False
        self.exceptions: Sequence[AaaException] = []
        self.parsed_files: Dict[Path, SourceFile] = {}
        self.verbose = False

    @staticmethod
    def without_file(code: str) -> "Runner":
        entry_point = Path("main.aaa")
        files = {entry_point: code}
        return Runner(entry_point, files)

    @staticmethod
    def compile_command(
        file_or_code: str,
        verbose: bool,
        binary_path: str,
        runtime_type_checks: bool,
    ) -> int:
        if file_or_code.endswith(".aaa"):
            runner = Runner(Path(file_or_code))
        else:
            runner = Runner.without_file(file_or_code)

        runner.set_verbose(verbose)

        return runner.run(
            compile=True,
            binary_path=Path(binary_path).resolve(),
            run=False,
            runtime_type_checks=runtime_type_checks,
            args=[],
        )

    @staticmethod
    def run_command(
        file_or_code: str,
        verbose: bool,
        runtime_type_checks: bool,
        args: Tuple[str],
    ) -> int:
        if file_or_code.endswith(".aaa"):
            runner = Runner(Path(file_or_code))
        else:
            runner = Runner.without_file(file_or_code)

        runner.set_verbose(verbose)

        return runner.run(
            compile=True,
            binary_path=None,
            run=True,
            runtime_type_checks=runtime_type_checks,
            args=list(args),
        )

    def add_parsed_files(self, parsed_files: Dict[Path, SourceFile]) -> None:
        self.parsed_files.update(parsed_files)

    def set_verbose(self, verbose: bool) -> None:
        self.verbose = verbose

    def _print_exceptions(self, runner_exception: AaaTranslationException) -> None:
        for exception in runner_exception.exceptions:
            print(exception, file=sys.stderr)
            print(file=sys.stderr)

        print(f"Found {len(runner_exception.exceptions)} error(s).", file=sys.stderr)

    def run(
        self,
        *,
        compile: bool,
        binary_path: Optional[Path],
        run: bool,
        runtime_type_checks: bool,
        args: List[str],
        **run_kwargs: Any,
    ) -> int:
        try:
            return self._run_process(
                compile=compile,
                binary_path=binary_path,
                run=run,
                args=args,
                runtime_type_checks=runtime_type_checks,
                **run_kwargs,
            ).returncode
        except ExcecutableDidNotRun:
            return 0
        except (AaaTranslationException, RustCompilerError, AaaException):
            return 1

    def _run_process(
        self,
        *,
        compile: bool,
        binary_path: Optional[Path],
        run: bool,
        runtime_type_checks: bool,
        args: List[str],
        **run_kwargs: Any,
    ) -> CompletedProcess[bytes]:
        transpiled = self.transpile(runtime_type_checks)

        if not compile:
            raise ExcecutableDidNotRun

        compiled = transpiled.compile(binary_path, self.verbose)

        if not run:
            raise ExcecutableDidNotRun

        return compiled.execute(args, **run_kwargs)

    def transpile(self, runtime_type_checks: bool) -> "Transpiled":
        transpiler_root = create_output_folder()

        try:
            parser = AaaParser(self.verbose)
            parser_output = parser.run(self.entrypoint, self.file_dict)
            cross_referencer_output = CrossReferencer(parser_output, self.verbose).run()

            type_checker = TypeChecker(cross_referencer_output, self.verbose)
            type_checker_output = type_checker.run()

            transpiler = Transpiler(
                cross_referencer_output=cross_referencer_output,
                type_checker_output=type_checker_output,
                transpiler_root=transpiler_root,
                runtime_type_checks=runtime_type_checks,
                verbose=self.verbose,
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
    completed_process = Runner(entrypoint)._run_process(
        compile=True,
        binary_path=binary_path,
        run=True,
        args=[],
        capture_output=True,
        runtime_type_checks=True,
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

        stdlib_impl_path = (Path(__file__).parent / "../../aaa-stdlib").resolve()

        cargo_toml.write_text(
            CARGO_TOML_TEMPLATE.format(stdlib_impl_path=stdlib_impl_path)
        )

        command = [
            "cargo",
            "build",
            "--release",
            "--quiet",
            "--manifest-path",
            str(cargo_toml),
        ]

        completed_process = subprocess.run(
            command, env=compiler_env, capture_output=True
        )

        exit_code = completed_process.returncode

        if verbose:
            print(completed_process.stdout.decode("utf-8"))
            print(completed_process.stderr.decode("utf-8"), file=sys.stderr)

        if exit_code != 0:
            raise RustCompilerError()

        default_binary_path = cargo_shared_target_dir / "release/aaa-stdlib-user"
        if binary_path:
            binary_path.parent.mkdir(exist_ok=True)
            binary_path = default_binary_path.rename(binary_path)

        return Compiled(binary_path or default_binary_path)


class Compiled:
    def __init__(self, binary_file: Path) -> None:
        self.binary_file = binary_file

    def execute(self, args: List[str], **run_kwargs: Any) -> CompletedProcess[bytes]:
        command = [str(self.binary_file)] + args
        return subprocess.run(command, **run_kwargs)

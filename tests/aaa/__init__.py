import os
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory, gettempdir
from typing import Dict, List, Optional, Sequence, Tuple, Type

from aaa import AaaException
from aaa.run import Runner


def check_aaa_main(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> Tuple[str, Sequence[AaaException]]:
    code = "fn main {\n" + code + "\n}"
    return check_aaa_full_source(code, expected_output, expected_exception_types)


def check_aaa_full_source(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> Tuple[str, Sequence[AaaException]]:
    files = {"main.aaa": code}
    return check_aaa_full_source_multi_file(
        files, expected_output, expected_exception_types
    )


def check_aaa_full_source_multi_file(
    files: Dict[str, str],
    expected_output: str,
    expected_exception_types: List[Type[Exception]],
) -> Tuple[str, Sequence[AaaException]]:
    with TemporaryDirectory() as directory:
        dir_path = Path(directory)
        for file, code in files.items():
            (dir_path / file).write_text(code)

        main_path = dir_path / "main.aaa"
        runner = Runner(main_path, None, False)

        binary = NamedTemporaryFile(delete=False).name

        with redirect_stdout(StringIO()) as stdout:
            with redirect_stderr(StringIO()) as stderr:
                runner_exit_code = runner.run(True, binary, False, [])

        if runner_exit_code == 0:
            process = subprocess.run([binary], capture_output=True)

            stdout.write(process.stdout.decode("utf-8"))
            stderr.write(process.stderr.decode("utf-8"))

        exception_types = list(map(type, runner.exceptions))

        if exception_types != expected_exception_types:
            # If we reach this code, some test for Aaa code is broken.
            # We print some info useful for debugging.

            error = (
                "\n"
                + "Expected exception types: "
                + " ".join(exc_type.__name__ for exc_type in expected_exception_types)
                + "\n"
                + "     Got exception types: "
                + " ".join(exc_type.__name__ for exc_type in exception_types)
                + "\n"
            )

            if runner.exceptions:
                error += "\nException(s):\n"

                for exception in runner.exceptions:
                    error += f"{exception}\n"

            assert False, error

        if not expected_exception_types:
            assert expected_output == stdout.getvalue()
            assert "" == stderr.getvalue()

        full_temp_dir = os.path.join(gettempdir(), directory)
    return full_temp_dir, runner.exceptions


# TODO #124 Refactor and remove redundant code for testing


def compile(source_path: Path) -> str:
    binary = NamedTemporaryFile(delete=False).name
    runner = Runner(source_path, None, False)
    exit_code = runner.run(True, binary, False, [])
    assert 0 == exit_code
    return binary


def run(binary: str, env: Optional[Dict[str, str]] = None) -> Tuple[str, str, int]:
    process = subprocess.run([binary], capture_output=True, timeout=2, env=env)

    stdout = process.stdout.decode("utf-8")
    stderr = process.stderr.decode("utf-8")
    exit_code = process.returncode

    return stdout, stderr, exit_code


def compile_run(source_path: Path) -> Tuple[str, str, int]:
    binary = compile(source_path)
    return run(binary)

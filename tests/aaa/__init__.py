from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Type

from lang.runtime.program import Program
from lang.runtime.simulator import Simulator


def check_aaa_main(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    code = "fn main {\n" + code + "\n}"
    check_aaa_full_source(code, expected_output, expected_exception_types)


def check_aaa_full_source(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    files = {"main.aaa": code}
    check_aaa_full_source_multi_file(files, expected_output, expected_exception_types)


def check_aaa_full_source_multi_file(
    files: Dict[str, str],
    expected_output: str,
    expected_exception_types: List[Type[Exception]],
) -> None:

    with TemporaryDirectory() as directory:
        dir_path = Path(directory)
        for file, code in files.items():
            (dir_path / file).write_text(code)

        main_path = dir_path / "main.aaa"
        program = Program(main_path)

        if not program.file_load_errors:
            Simulator(program).run()

            with redirect_stdout(StringIO()) as stdout:
                with redirect_stderr(StringIO()) as stderr:
                    Simulator(program).run()

        exception_types = list(map(type, program.file_load_errors))
        assert exception_types == expected_exception_types

        if not expected_exception_types:
            assert expected_output == stdout.getvalue()
            assert "" == stderr.getvalue()

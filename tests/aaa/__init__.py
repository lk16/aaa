from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Tuple, Type

from lang.exceptions import AaaException, AaaRuntimeException
from lang.runtime.program import Program
from lang.runtime.simulator import Simulator


def check_aaa_main(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> Tuple[str, List[AaaException]]:
    code = "fn main {\n" + code + "\n}"
    return check_aaa_full_source(code, expected_output, expected_exception_types)


def check_aaa_full_source(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> Tuple[str, List[AaaException]]:
    files = {"main.aaa": code}
    return check_aaa_full_source_multi_file(
        files, expected_output, expected_exception_types
    )


def check_aaa_full_source_multi_file(
    files: Dict[str, str],
    expected_output: str,
    expected_exception_types: List[Type[Exception]],
) -> Tuple[str, List[AaaException]]:

    with TemporaryDirectory() as directory:
        dir_path = Path(directory)
        for file, code in files.items():
            (dir_path / file).write_text(code)

        main_path = dir_path / "main.aaa"
        program = Program(main_path)

        exceptions: List[AaaException] = []
        exceptions += program.file_load_errors

        if not exceptions:
            with redirect_stdout(StringIO()) as stdout:
                with redirect_stderr(StringIO()) as stderr:
                    try:
                        Simulator(program).run(raise_=True)
                    except AaaRuntimeException as e:
                        exceptions = [e]

    exception_types = list(map(type, program.file_load_errors))

    assert exception_types == expected_exception_types

    if not expected_exception_types:
        assert expected_output == stdout.getvalue()
        assert "" == stderr.getvalue()

    return directory, exceptions

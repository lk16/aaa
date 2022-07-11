from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import List, Type

from lang.runtime.program import Program
from lang.runtime.simulator import Simulator


def check_aaa_code(
    code: str, expected_output: str, expected_exception_types: List[Type[Exception]]
) -> None:
    code = "fn main {\n" + code + "\n}"
    program = Program.without_file(code)
    assert not program.file_load_errors
    Simulator(program).run()

    with redirect_stdout(StringIO()) as stdout:
        with redirect_stderr(StringIO()) as stderr:
            Simulator(program).run()

    assert list(map(type, program.file_load_errors)) == expected_exception_types

    if not expected_exception_types:
        assert expected_output == stdout.getvalue()
        assert "" == stderr.getvalue()

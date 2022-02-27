from pathlib import Path

from lang.parse import parse
from lang.program import Program


def run_file(file_path: str, verbose: bool = False) -> None:
    code = Path(file_path).read_text()
    run_code(file_path, code, verbose)


def run_code(file_path: str, code: str, verbose: bool = False) -> None:
    # TODO use file_path for debug/error messages
    _ = file_path

    parsed_file = parse(code)
    program = Program(parsed_file.functions, verbose)
    program.run()


def run_code_as_main(main_body_code: str, verbose: bool = False) -> None:
    code = f"fn main begin\n{main_body_code}\nend"
    file_path = "<stdin>"
    run_code(file_path, code, verbose)

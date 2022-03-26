from pathlib import Path

from lang.parse import parse
from lang.simulator import Simulator


def run_file(filename: str, verbose: bool = False) -> None:
    code = Path(filename).read_text()
    run_code(filename, code, verbose)


def run_code(filename: str, code: str, verbose: bool = False) -> None:

    parsed_file = parse(filename, code)
    simulator = Simulator(parsed_file.functions, verbose)
    simulator.run()


def run_code_as_main(main_body_code: str, verbose: bool = False) -> None:
    code = f"fn main begin\n{main_body_code}\nend"
    filename = "<stdin>"
    run_code(filename, code, verbose)

#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from lang.program import Program
from lang.simulator import Simulator

GRAMMAR_FILE_PATH = Path("grammar.txt")


def run(file_path: str, verbose_flag: Optional[str] = None) -> None:

    verbose = False

    if verbose_flag:  # TODO allow any order of flags and commands
        if verbose_flag == "-v":
            verbose = True
        else:
            raise ArgParseError("Unexpected option for run.")

    program = Program(Path(file_path))
    simulator = Simulator(program, verbose)
    simulator.run()


def cmd(code: str, verbose_flag: Optional[str] = None) -> None:

    verbose = False

    if verbose_flag:  # TODO allow any order of flags and commands
        if verbose_flag == "-v":
            verbose = True
        else:
            raise ArgParseError("Unexpected option for cmd.")

    code = f"fn main begin {code}\n end"
    program = Program.without_file(code)
    simulator = Simulator(program, verbose)
    simulator.run()


def runtests(*args: Any) -> None:
    if args:
        raise ArgParseError("runtests expects no flags or arguments.")

    commands = [
        "check_parser_staleness lang/grammar/grammar.txt lang/grammar/parser.py",
        "pre-commit run --all-files mypy",
        "pytest --cov=lang --cov-report=term-missing --pdb -x -vv",
    ]

    for command in commands:
        proc = subprocess.run(command.split())
        if proc.returncode != 0:
            print(f'Command "{command}" failed.', file=sys.stderr)
            exit(1)


COMMANDS: Dict[str, Callable[..., None]] = {
    "cmd": cmd,
    "run": run,
    "runtests": runtests,
}


class ArgParseError(Exception):
    ...


def show_usage(argv: List[str], error_message: str) -> None:
    message = (
        f"Argument parsing failed: {error_message}\n\n"
        + "Available commands:\n"
        + f"{argv[0]} cmd CODE <-v>\n"
        + f"{argv[0]} run FILE_PATH <-v>\n"
        + f"{argv[0]} runtests\n"
    )

    print(message, file=sys.stderr)


def main(argv: List[str]) -> int:
    if len(argv) == 1:
        show_usage(argv, "Missing command")
        return 1

    command_key = argv[1]
    command_args = argv[2:]

    try:
        command = COMMANDS[command_key]
    except KeyError:
        show_usage(argv, f"No command {command_key}.")
        return 1

    try:
        command(*command_args)
    except ArgParseError as e:
        show_usage(argv, e.args[0])
        return 1

    return 0


if __name__ == "__main__":
    exit(main(sys.argv))

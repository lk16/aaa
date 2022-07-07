#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from lang.runtime.program import Program
from lang.runtime.simulator import Simulator


def run(file_path: str, verbose_flag: Optional[str] = None) -> None:

    verbose = False

    if verbose_flag:
        if verbose_flag == "-v":
            verbose = True
        else:
            raise ArgParseError("Unexpected option for run.")

    program = Program(Path(file_path))
    program.exit_on_error()
    simulator = Simulator(program, verbose)
    simulator.run()


def cmd(code: str, verbose_flag: Optional[str] = None) -> None:
    code = f"fn main begin {code}\n end"
    cmd_full(code, verbose_flag)


def cmd_full(code: str, verbose_flag: Optional[str] = None) -> None:

    verbose = False

    if verbose_flag:
        if verbose_flag == "-v":
            verbose = True
        else:
            raise ArgParseError("Unexpected option for cmd.")

    program = Program.without_file(code)
    program.exit_on_error()
    simulator = Simulator(program, verbose)
    simulator.run()


def runtests(*args: Any) -> None:
    if args:
        raise ArgParseError("runtests expects no flags or arguments.")

    commands = [
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
    "cmd-full": cmd_full,
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
        + f"{argv[0]} cmd-full CODE <-v>\n"
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

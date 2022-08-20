#!/usr/bin/env -S python3 -u

import os
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Dict, List, Optional

from lang.cross_referencer.cross_referencer import CrossReferencer
from lang.parser.parser import Parser
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
    code = "fn main {\n" + code + "\n}"
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


def cmd_new(code: str) -> None:
    # TODO the other functions here should be refactored
    # TODO This should be remove before the separate-steps branch is merged

    try:
        stdlib_path = Path(os.environ["AAA_STDLIB_PATH"]) / "builtins.aaa"
    except KeyError:
        print(
            "Environment variable AAA_STDLIB_PATH is not set. Cannot find standard library!",
            file=sys.stderr,
        )
        exit(1)

    with NamedTemporaryFile() as temp_file:
        file = Path(temp_file.name)
        file.write_text(code)

        parser_output = Parser(file, stdlib_path).run()
        CrossReferencer(parser_output).run()


def runtests(*args: Any) -> None:
    if args:
        raise ArgParseError("runtests expects no flags or arguments.")

    commands = [
        "pre-commit run --all-files mypy",
        "pytest --cov=lang --cov-report=term-missing --pdb -x --lf --nf",
    ]

    for command in commands:
        proc = subprocess.run(command.split())
        if proc.returncode != 0:
            print(f'Command "{command}" failed.', file=sys.stderr)
            exit(1)


COMMANDS: Dict[str, Callable[..., None]] = {
    "cmd": cmd,
    "cmd-new": cmd_new,
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
        + f"{argv[0]} cmd-new CODE\n"
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

#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from lang.instructions import get_instructions
from lang.parse import parse as new_parse
from lang.run import run_code_as_main, run_file  # TODO remove alias

GRAMMAR_FILE_PATH = Path("grammar.txt")


def run(file_path: str, verbose_flag: Optional[str] = None) -> None:

    verbose = False

    if verbose_flag:  # TODO allow any order of flags and commands
        if verbose_flag == "-v":
            verbose = True
        else:
            raise ArgParseError("Unexpected option for run.")

    try:
        run_file(file_path, verbose)
    except OSError:
        print(f'Could not open or read "{file_path}"', file=sys.stderr)
        exit(1)


def cmd(code: str, verbose_flag: Optional[str] = None) -> None:

    verbose = False

    if verbose_flag:  # TODO allow any order of flags and commands
        if verbose_flag == "-v":
            verbose = True
        else:
            raise ArgParseError("Unexpected option for cmd.")

    run_code_as_main(code, verbose)


def runtests(*args: Any) -> None:
    if args:
        raise ArgParseError("runtests expects no flags or arguments.")

    commands = [
        "pre-commit run --all-files mypy",
        "pytest --cov=lang --cov-report=term-missing --pdb -x",
    ]

    for command in commands:
        proc = subprocess.run(command.split())
        if proc.returncode != 0:
            exit(1)


def try_instruction_generator(*args: Any) -> None:
    if args:
        raise ArgParseError("try-instruction-generator expects no flags or arguments.")

    while True:
        code = input("> ")
        code = f"fn main begin\n{code}\nend"
        try:
            file = new_parse(code)
        except Exception:
            print("Parse failed")
            continue

        main = file.functions["main"]
        instructions = get_instructions(main)

        print()

        for ip, instruction in enumerate(instructions):
            print(f"{ip:>5} |", instruction.__repr__())

        print()


COMMANDS: Dict[str, Callable[..., None]] = {
    "cmd": cmd,
    "run": run,
    "runtests": runtests,
    "try-instruction-generator": try_instruction_generator,
    # TODO add repl() command
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
        + f"{argv[0]} try-instruction-generator\n"
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

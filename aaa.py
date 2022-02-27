#!/usr/bin/env python3

import subprocess
import sys
from parser.grammar_generator import check_grammar_file_staleness
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from lang.grammar import REWRITE_RULES, ROOT_SYMBOL
from lang.instructions import get_instructions
from lang.parse import parse as new_parse  # TODO remove alias

GRAMMAR_FILE_PATH = Path("grammar.txt")


def run_(filename: str, verbose_flag: Optional[str] = None) -> None:

    verbose = False

    if verbose_flag:
        if verbose_flag == "-v":
            verbose = True
        else:
            raise ArgParseError("Unexpected option for cmd.")

    with open(filename, "r") as f:
        code = f.read()

    # TODO
    _ = code
    _ = verbose
    raise NotImplementedError


def cmd(code: str, verbose_flag: Optional[str] = None) -> None:

    verbose = False

    if verbose_flag:
        if verbose_flag == "-v":
            verbose = True
        else:
            raise ArgParseError("Unexpected option for cmd.")

    code = "fn main begin\n" + code + "\nend"

    # TODO
    _ = verbose
    raise NotImplementedError


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


def generate_grammar_file(*args: Any) -> None:
    if args:
        raise ArgParseError("generate-grammar-file expects no flags or arguments.")

    stale, new_grammar = check_grammar_file_staleness(
        GRAMMAR_FILE_PATH, REWRITE_RULES, ROOT_SYMBOL
    )

    if stale:
        GRAMMAR_FILE_PATH.write_text(new_grammar)
        print(f"{GRAMMAR_FILE_PATH.name} was created or updated.")
    else:
        print(f"{GRAMMAR_FILE_PATH.name} was up-to-date.")


COMMANDS: Dict[str, Callable[..., None]] = {
    "cmd": cmd,
    "generate-grammar-file": generate_grammar_file,
    "run": run_,
    "runtests": runtests,
    "try-instruction-generator": try_instruction_generator,
}


class ArgParseError(Exception):
    ...


def show_usage(argv: List[str], error_message: str) -> None:
    message = (
        f"Argument parsing failed: {error_message}\n\n"
        + "Available commands:\n"
        + f"{argv[0]} cmd CODE <-v>\n"
        + f"{argv[0]} run FILE <-v>\n"
        + f"{argv[0]} generate-grammar-file\n"
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

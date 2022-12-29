#!/usr/bin/env -S python3 -u

import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

import click
from click import ClickException

from aaa.run import Runner
from aaa.run_tests import TestRunner


@click.group()
def cli() -> None:
    ...


@cli.command()
@click.argument("code", type=str)
@click.option("-v", "--verbose", is_flag=True)
def cmd(code: str, verbose: bool) -> None:
    runner = Runner.without_file(code, None, verbose)
    exit_code = runner.run(None, True, None, True)
    exit(exit_code)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("-v", "--verbose", is_flag=True)
def run(path: str, verbose: bool) -> None:
    runner = Runner(Path(path), None, verbose)
    exit_code = runner.run(None, True, None, True)
    exit(exit_code)


@cli.command()
def runtests() -> None:
    binary_path = Path(NamedTemporaryFile(delete=False).name)

    commands = [
        "pre-commit run --all-files mypy",
        "pytest --cov=aaa --cov-report=term-missing --pdb -x --lf --nf",
        f"./manage.py test stdlib/ --compile --binary {binary_path}",
        f"valgrind --error-exitcode=1 --leak-check=full {binary_path}",
    ]

    for command in commands:
        proc = subprocess.run(command.split())
        if proc.returncode != 0:
            raise ClickException(f'Command "{command}" failed.')


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("-c", "--compile", is_flag=True)
@click.option("-r", "--run", is_flag=True)
@click.option("--c-file")
@click.option("-o", "--binary")
@click.option("-v", "--verbose", is_flag=True)
def test(
    path: str,
    compile: bool,
    run: bool,
    verbose: bool,
    c_file: Optional[str],
    binary: Optional[str],
) -> None:
    if c_file is not None and not c_file.endswith(".c"):
        print("Output C file should have a .c extension.", file=sys.stderr)
        exit(1)

    if binary is not None and not compile:
        print(
            "Specifying binary path without compiling does not make sense.",
            file=sys.stderr,
        )
        exit(1)

    if run and not compile:  # pragma: nocover
        print("Can't run binary without (re-)compiling!", file=sys.stderr)
        exit(1)

    # TODO move building of main test file to Runner
    test_runner = TestRunner(Path(path), verbose)
    main_test_code = test_runner.build_main_test_file()

    main_test_file = Path(NamedTemporaryFile(delete=False).name)
    main_test_file.write_text(main_test_code)

    runner = Runner(main_test_file, test_runner.parsed_files, verbose)

    # TODO move a lot of this code out of manage.py
    generated_c_file: Optional[Path] = None
    if c_file:
        generated_c_file = Path(c_file).resolve()

    generated_binary_file: Optional[Path] = None
    if binary:
        generated_binary_file = Path(binary).resolve()

    exit_code = runner.run(generated_c_file, compile, generated_binary_file, run)
    exit(exit_code)


if __name__ == "__main__":
    cli()

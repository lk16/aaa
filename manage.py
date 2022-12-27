#!/usr/bin/env -S python3 -u

import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir

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
    commands = [
        "pre-commit run --all-files mypy",
        "pytest --cov=aaa --cov-report=term-missing --pdb -x --lf --nf",
        "./manage.py transpile-tests stdlib/ generated.c --compile",
        "valgrind --error-exitcode=1 --leak-check=full ./generated",
    ]

    for command in commands:
        proc = subprocess.run(command.split())
        if proc.returncode != 0:
            raise ClickException(f'Command "{command}" failed.')


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("-c", "--compile", is_flag=True)
@click.option("-r", "--run", is_flag=True)
@click.option("-v", "--verbose", is_flag=True)
def test(path: str, compile: bool, run: bool, verbose: bool) -> None:
    # TODO add flag for generated c file and generated binary file

    # TODO move building of main test file to Runner
    test_runner = TestRunner(Path(path), verbose)
    main_test_code = test_runner.build_main_test_file()

    main_test_file = Path(gettempdir()) / NamedTemporaryFile(delete=False).name
    main_test_file.write_text(main_test_code)

    runner = Runner(main_test_file, test_runner.parsed_files, verbose)
    exit_code = runner.run(None, compile, None, run)
    exit(exit_code)


if __name__ == "__main__":
    cli()

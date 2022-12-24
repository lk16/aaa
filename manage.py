#!/usr/bin/env -S python3 -u

import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir

import click
from click import ClickException

from aaa.run import Runner
from aaa.run_tests import TestRunner
from aaa.tokenizer.tokenizer import Tokenizer


@click.group()
def cli() -> None:
    ...


@cli.command()
@click.argument("code", type=str)
@click.option("-v", "--verbose", is_flag=True)
def cmd(code: str, verbose: bool) -> None:
    exit_code = Runner.without_file(code).run(verbose)
    exit(exit_code)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("-v", "--verbose", is_flag=True)
def run(path: str, verbose: bool) -> None:
    exit_code = Runner(Path(path)).run(verbose)
    exit(exit_code)


@cli.command()
@click.argument("source_file", type=click.Path(exists=True))
@click.argument("output_file")
@click.option("-c", "--compile", is_flag=True)
@click.option("-r", "--run", is_flag=True)
@click.option("-v", "--verbose", is_flag=True)
def transpile(
    source_file: str, output_file: str, compile: bool, run: bool, verbose: bool
) -> None:
    runner = Runner(Path(source_file))
    exit_code = runner.transpile(Path(output_file), compile, run, verbose)
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
@click.option("-v", "--verbose", is_flag=True)
def test(path: str, verbose: bool) -> None:
    exit_code = TestRunner(Path(path)).run()
    exit(exit_code)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.argument("output_file")
@click.option("-c", "--compile", is_flag=True)
@click.option("-r", "--run", is_flag=True)
@click.option("-v", "--verbose", is_flag=True)
def transpile_tests(
    path: str, output_file: str, compile: bool, run: bool, verbose: bool
) -> None:
    # TODO add verbose flag

    test_runner = TestRunner(Path(path))
    main_test_code = test_runner.build_main_test_file()

    main_test_file = Path(gettempdir()) / NamedTemporaryFile(delete=False).name
    main_test_file.write_text(main_test_code)

    runner = Runner(main_test_file, test_runner.parsed_files)
    exit_code = runner.transpile(Path(output_file), compile, run, verbose)
    exit(exit_code)


# TODO remove
@cli.command()
@click.argument("path", type=click.Path(exists=True))
def tokenize(path: str) -> None:
    Tokenizer(Path(path)).run()


if __name__ == "__main__":
    cli()

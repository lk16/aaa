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
def cmd(code: str) -> None:
    # TODO add verbose flag
    exit_code = Runner.without_file(code).run()
    exit(exit_code)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
def run(path: str) -> None:
    # TODO add verbose flag
    exit_code = Runner(Path(path)).run()
    exit(exit_code)


@cli.command()
@click.argument("source_file", type=click.Path(exists=True))
@click.argument("output_file")
@click.option("-c", "--compile", is_flag=True, default=False)
@click.option("-r", "--run", is_flag=True, default=False)
def transpile(source_file: str, output_file: str, compile: bool, run: bool) -> None:
    # TODO add verbose flag
    exit_code = Runner(Path(source_file)).transpile(
        Path(output_file), compile=compile, run=run
    )
    exit(exit_code)


@cli.command()
def runtests() -> None:
    commands = [
        "pre-commit run --all-files mypy",
        "pytest --cov=aaa --cov-report=term-missing --pdb -x --lf --nf",
    ]

    for command in commands:
        proc = subprocess.run(command.split())
        if proc.returncode != 0:
            raise ClickException(f'Command "{command}" failed.')


@cli.command()
@click.argument("path", type=click.Path(exists=True))
def test(path: str) -> None:
    # TODO add verbose flag
    exit_code = TestRunner(Path(path)).run()
    exit(exit_code)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.argument("output_file")
@click.option("-c", "--compile", is_flag=True, default=False)
@click.option("-r", "--run", is_flag=True, default=False)
def transpile_tests(path: str, output_file: str, compile: bool, run: bool) -> None:
    # TODO add verbose flag

    main_test_code = TestRunner(Path(path)).build_main_test_file()

    main_test_file = Path(gettempdir()) / NamedTemporaryFile(delete=False).name
    main_test_file.write_text(main_test_code)

    exit_code = Runner(main_test_file).transpile(
        Path(output_file), compile=compile, run=run
    )
    exit(exit_code)


if __name__ == "__main__":
    cli()

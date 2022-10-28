#!/usr/bin/env -S python3 -u

import subprocess
from pathlib import Path

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
    exit_code = Runner.without_file(code).run()
    exit(exit_code)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
def run(path: str) -> None:
    exit_code = Runner(Path(path)).run()
    exit(exit_code)


@cli.command()
@click.argument("source_file", type=click.Path(exists=True))
@click.argument("output_file")
def transpile(source_file: str, output_file: str) -> None:
    exit_code = Runner(Path(source_file)).transpile(Path(output_file))
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
    exit_code = TestRunner(Path(path)).run()
    exit(exit_code)


if __name__ == "__main__":
    cli()

#!/usr/bin/env -S python3 -u

import subprocess
from pathlib import Path

import click
from click import ClickException

from aaa.run import Runner


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
def runtests() -> None:
    commands = [
        "pre-commit run --all-files mypy",
        "pytest --cov=lang --cov-report=term-missing --pdb -x --lf --nf",
    ]

    for command in commands:
        proc = subprocess.run(command.split())
        if proc.returncode != 0:
            raise ClickException(f'Command "{command}" failed.')


if __name__ == "__main__":
    cli()

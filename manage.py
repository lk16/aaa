#!/usr/bin/env -S python3 -u

import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir

import click
from click import ClickException

from aaa.run import Runner


@click.group()
def cli() -> None:
    ...


@cli.command()
@click.argument("code", type=str)
def cmd(code: str) -> None:
    with NamedTemporaryFile(delete=False) as temp_file:
        file = Path(gettempdir()) / temp_file.name
        file.write_text(code)
        exit_code = Runner(file).run()

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

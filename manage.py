#!/usr/bin/env -S python3 -u

import os
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile

import click
from click import ClickException

from lang.cross_referencer.cross_referencer import CrossReferencer
from lang.parser.parser import Parser


@click.group()
def cli() -> None:
    ...


@cli.command()
@click.argument("code", type=str)
def cmd(code: str) -> None:
    try:
        stdlib_path = Path(os.environ["AAA_STDLIB_PATH"]) / "builtins.aaa"
    except KeyError as e:
        raise ClickException(
            "Environment variable AAA_STDLIB_PATH is not set. Cannot find standard library!",
        ) from e

    with NamedTemporaryFile() as temp_file:
        file = Path(temp_file.name)
        file.write_text(code)

        parser_output = Parser(file, stdlib_path).run()
        CrossReferencer(parser_output).run()


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

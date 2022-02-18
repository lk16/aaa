#!/usr/bin/env python3

import subprocess

import click

from lang.parse import parse
from lang.run import run_program


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument("file", type=click.Path(exists=True))
def run(file: str) -> None:
    with open(file, "r") as f:
        code = f.read()

    program = parse(code)
    run_program(program)


@cli.command()
@click.argument("code", type=str)
def cmd(code: str) -> None:
    program = parse(code)
    run_program(program)


@cli.command()
def runtests() -> None:
    subprocess.run("pytest --cov=lang --cov-report=term-missing --pdb".split())


if __name__ == "__main__":
    cli()

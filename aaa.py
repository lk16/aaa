#!/usr/bin/env python3

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


if __name__ == "__main__":
    cli()

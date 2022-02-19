#!/usr/bin/env python3

import subprocess

import click

from lang.parse import parse
from lang.run import run_program
from lang.tokenize import tokenize


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument("filename", type=click.Path(exists=True))
def run(filename: str) -> None:
    with open(filename, "r") as f:
        code = f.read()

    tokens = tokenize(code, filename)
    program = parse(tokens)
    run_program(program)


@cli.command()
@click.argument("code", type=str)
@click.option("--verbose/--no-verbose", "-v", type=bool)
def cmd(code: str, verbose: bool) -> None:
    tokens = tokenize(code, "<stdin>")
    program = parse(tokens)
    run_program(program, verbose=verbose)

    if verbose:
        print()


@cli.command()
def runtests() -> None:
    subprocess.run("pytest --cov=lang --cov-report=term-missing --pdb".split())


if __name__ == "__main__":
    cli()

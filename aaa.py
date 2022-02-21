#!/usr/bin/env python3

import subprocess

import click

from lang.new_tokenizer import new_parse
from lang.parse import parse
from lang.run import run
from lang.tokenize import tokenize


@click.group()
def cli() -> None:
    pass


@cli.command(name="run")
@click.argument("filename", type=click.Path(exists=True))
@click.option("--verbose/--no-verbose", "-v", type=bool)
def run_(filename: str, verbose: bool) -> None:
    with open(filename, "r") as f:
        code = f.read()

    tokens = tokenize(code, filename)
    program = parse(tokens)
    run(program, verbose=verbose)


@cli.command()
@click.argument("code", type=str)
@click.option("--verbose/--no-verbose", "-v", type=bool)
def cmd(code: str, verbose: bool) -> None:
    code = "fn main begin\n" + code + "\nend"
    tokens = tokenize(code, "<stdin>")
    program = parse(tokens)
    run(program, verbose=verbose)

    if verbose:
        print()


@cli.command()
def runtests() -> None:
    commands = [
        "pre-commit run --all-files",
        "pytest --cov=lang --cov-report=term-missing --pdb -x",
    ]

    for command in commands:
        subprocess.run(command.split())


@cli.command()
def try_new_tokenizer() -> None:
    while True:
        code = input("> ")
        result = new_parse(code)
        print(f"Parse result: {result}")
        print()


if __name__ == "__main__":
    cli()

#!/usr/bin/env -S python3 -u

import subprocess
from pathlib import Path
from typing import Optional, Tuple

import click
from click import ClickException

from aaa.runner.runner import Runner
from aaa.runner.test_runner import TestRunner


@click.group()
def cli() -> None:
    ...


@cli.command()
@click.argument("code", type=str)
@click.option("-c", "--compile", is_flag=True)
@click.option("-r", "--run", is_flag=True)
@click.option("-o", "--binary")
@click.option("-v", "--verbose", is_flag=True)
@click.argument("args", nargs=-1)
def cmd(
    code: str,
    compile: bool,
    run: bool,
    verbose: bool,
    binary: Optional[str],
    args: Tuple[str],
) -> None:
    runner = Runner.without_file(code)
    runner.set_verbose(verbose)

    if binary:
        binary_path = Path(binary).resolve()
    else:
        binary_path = None

    exit_code = runner.run(
        compile=compile, binary_path=binary_path, run=run, args=list(args)
    )

    exit(exit_code)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("-c", "--compile", is_flag=True)
@click.option("-r", "--run", is_flag=True)
@click.option("-o", "--binary")
@click.option("-v", "--verbose", is_flag=True)
@click.argument("args", nargs=-1)
def run(
    path: str,
    compile: bool,
    run: bool,
    verbose: bool,
    binary: Optional[str],
    args: Tuple[str],
) -> None:
    runner = Runner(Path(path))
    runner.set_verbose(verbose)

    if binary:
        binary_path = Path(binary).resolve()
    else:
        binary_path = None

    exit_code = runner.run(
        compile=compile, binary_path=binary_path, run=run, args=list(args)
    )

    exit(exit_code)


@cli.command()
def runtests() -> None:
    commands = [
        "pre-commit run --all-files mypy",
        "pytest --cov=aaa --cov-report=term-missing --pdb -x --lf --nf",
        f"./manage.py test stdlib/ --compile --run",
    ]

    for command in commands:
        print(f"Running: {command}")
        proc = subprocess.run(command.split())
        if proc.returncode != 0:
            raise ClickException(f"Command failed: {command}")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("-c", "--compile", is_flag=True)
@click.option("-r", "--run", is_flag=True)
@click.option("-o", "--binary")
@click.option("-v", "--verbose", is_flag=True)
def test(
    path: str, compile: bool, run: bool, verbose: bool, binary: Optional[str]
) -> None:
    test_runner = TestRunner(path)
    test_runner.set_verbose(verbose)

    if binary:
        binary_path = Path(binary)
    else:
        binary_path = None

    exit_code = test_runner.run(compile=compile, binary=binary_path, run=run)
    exit(exit_code)


if __name__ == "__main__":
    cli()

#!/usr/bin/env -S python3 -u

import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, Tuple

import click
from click import ClickException

from aaa.run import Runner
from aaa.run_tests import TestRunner


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
    runner = Runner.without_file(code, None, verbose)
    exit_code = runner.run(compile, binary, run, list(args))
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
    runner = Runner(Path(path), None, verbose)
    exit_code = runner.run(compile, binary, run, list(args))
    exit(exit_code)


@cli.command()
def runtests() -> None:
    binary_path = Path(NamedTemporaryFile(delete=False).name)

    commands = [
        "pre-commit run --all-files mypy",
        "pytest --cov=aaa --cov-report=term-missing --pdb -x --lf --nf",
        f"./manage.py test stdlib/ --compile --binary {binary_path}",
        f"{binary_path}",
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
    test_runner = TestRunner(Path(path), verbose)
    exit_code = test_runner.run(compile, binary, run)
    exit(exit_code)


if __name__ == "__main__":
    cli()

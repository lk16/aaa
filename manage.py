#!/usr/bin/env -S python3 -u

import subprocess
from pathlib import Path
from typing import Any, Optional

import click
from click import ClickException

from aaa.runner.runner import Runner
from aaa.runner.test_runner import TestRunner


@click.group()
def cli() -> None:
    ...


@cli.command()
@click.argument("file_or_code", type=str)
@click.argument("binary_path", type=str)
@click.option("-v", "--verbose", is_flag=True)
@click.option("-t", "--runtime-type-checks", is_flag=True)
def compile(**kwargs: Any) -> None:
    exit(Runner.compile_command(**kwargs))


@cli.command()
@click.argument("file_or_code", type=str)
@click.option("-t", "--runtime-type-checks", is_flag=True)
@click.option("-v", "--verbose", is_flag=True)
@click.argument("args", nargs=-1)
def run(**kwargs: Any) -> None:
    exit(Runner.run_command(**kwargs))


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
@click.option("-t", "--runtime-type-checks", is_flag=True)
@click.option("-v", "--verbose", is_flag=True)
def test(
    path: str,
    compile: bool,
    run: bool,
    verbose: bool,
    binary: Optional[str],
    runtime_type_checks: bool,
) -> None:
    test_runner = TestRunner(path)
    test_runner.set_verbose(verbose)

    if binary:
        binary_path = Path(binary)
    else:
        binary_path = None

    exit_code = test_runner.run(
        compile=compile,
        binary=binary_path,
        run=run,
        runtime_type_checks=runtime_type_checks,
    )
    exit(exit_code)


if __name__ == "__main__":
    cli()

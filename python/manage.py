#!/usr/bin/env -S python3 -u

from typing import Any

import click

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
@click.argument("path", type=click.Path(exists=True))
@click.option("-o", "--binary")
@click.option("-t", "--runtime-type-checks", is_flag=True)
@click.option("-v", "--verbose", is_flag=True)
def test(**kwargs: Any) -> None:
    exit(TestRunner.test_command(**kwargs))


if __name__ == "__main__":
    cli()

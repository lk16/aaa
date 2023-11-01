#!/usr/bin/env -S python3 -u

import os
from pathlib import Path
from typing import Any, Optional, Tuple

import click

from aaa.formatter import format_source_files
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


@cli.command()
@click.argument("files", type=click.Path(exists=True), nargs=-1)
@click.option("--fix", is_flag=True, default=False)
@click.option("--show-diff", is_flag=True, default=False)
@click.option("--stdlib-path", type=click.Path(exists=True))
def format(
    files: Tuple[str], fix: bool, show_diff: bool, stdlib_path: Optional[str]
) -> None:
    if stdlib_path:
        os.environ["AAA_STDLIB_PATH"] = str(Path(stdlib_path).resolve())

    exit_code = format_source_files(files, fix, show_diff)
    exit(exit_code)


if __name__ == "__main__":
    cli()

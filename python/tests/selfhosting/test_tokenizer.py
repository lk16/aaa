import secrets
import subprocess
from glob import glob
from pathlib import Path
from tempfile import gettempdir

import pytest
from _pytest.mark.structures import ParameterSet
from pytest import CaptureFixture

from aaa import aaa_project_root
from aaa.parser.parser import aaa_file_parser
from aaa.runner.runner import Runner


def tokenize_with_python(aaa_file: Path) -> str:
    tokens = aaa_file_parser.tokenize_file(aaa_file, filter_token_types=True)

    output = ""
    for token in tokens:
        position = token.position
        output += f"{position.file}:{position.line}:{position.column}"
        output += f" {token.type} {token.value}\n"

    return output


@pytest.fixture(scope="session")
def tokenizer_excecutable() -> str:
    binary_folder = Path(gettempdir()) / "aaa/transpiled/tests"
    binary_path = binary_folder / "".join(
        secrets.choice("0123456789abcdef") for _ in range(16)
    )

    exit_code = Runner.compile_command(
        file_or_code="../examples/selfhosting/tokenizer.aaa",
        verbose=False,
        binary_path=str(binary_path),
        runtime_type_checks=True,
    )

    assert exit_code == 0
    return str(binary_path)


def aaa_source_files() -> tuple[list[str], list[ParameterSet]]:
    return (
        ["source_file"],
        [
            pytest.param(Path(file).resolve(), id=str(file))
            for file in glob("**/*.aaa", root_dir=aaa_project_root(), recursive=True)
        ],
    )


@pytest.mark.parametrize(*aaa_source_files())
def test_tokenizer_output(
    tokenizer_excecutable: str, capfd: CaptureFixture[str], source_file: Path
) -> None:
    completed_process = subprocess.run([tokenizer_excecutable, str(source_file)])
    assert completed_process.returncode == 0

    captured = capfd.readouterr()
    assert captured.out == tokenize_with_python(source_file)
    assert captured.err == ""

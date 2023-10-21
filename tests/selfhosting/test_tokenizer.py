from pathlib import Path

from pytest import CaptureFixture

from aaa.runner.runner import Runner
from aaa.tokenizer.tokenizer import Tokenizer


def tokenize_with_python(aaa_file: Path) -> str:
    tokenizer = Tokenizer(aaa_file, False)
    tokens = tokenizer.run()

    output = ""
    for token in tokens:
        position = token.position
        output += f"{position.file}:{position.line}:{position.column}"
        output += f" {token.type.value} {token.value}\n"

    return output


def test_tokenizer_output(capfd: CaptureFixture[str]) -> None:
    entrypoint = Path("examples/selfhosting/tokenizer.aaa")

    runner = Runner(entrypoint)
    exit_code = runner.run(
        compile=True,
        binary_path=None,
        run=True,
        args=[str(entrypoint)],
        runtime_type_checks=True,
    )

    assert exit_code == 0

    captured = capfd.readouterr()
    assert captured.out == tokenize_with_python(entrypoint)
    assert captured.err == ""

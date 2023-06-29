from pathlib import Path

from pytest import CaptureFixture

from aaa.run import Runner
from aaa.run_tests import TestRunner
from aaa.tokenizer.tokenizer import Tokenizer


def test_tokenizer_unittests() -> None:
    test_runner = TestRunner(Path("examples/selfhosting"), False)
    exit_code = test_runner.run(True, None, True)

    assert exit_code == 0


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
    tokenizer_source_file = Path("examples/selfhosting/tokenizer.aaa")

    runner = Runner(tokenizer_source_file, {}, False)
    exit_code = runner.run(True, None, True, [str(tokenizer_source_file)])

    assert exit_code == 0

    captured = capfd.readouterr()
    assert captured.out == tokenize_with_python(tokenizer_source_file)
    assert captured.err == ""

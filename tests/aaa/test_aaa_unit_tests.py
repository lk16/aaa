import pytest

from aaa.runner.test_runner import TestRunner


@pytest.mark.skip()  # TODO
def test_tokenizer_unittests() -> None:
    exit_code = TestRunner.test_command(
        ".", verbose=False, binary=None, runtime_type_checks=True
    )
    assert exit_code == 0

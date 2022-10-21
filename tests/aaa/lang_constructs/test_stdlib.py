import os
from pathlib import Path

from pytest import CaptureFixture

from aaa.run_tests import TestRunner


def test_stdlib(capsys: CaptureFixture[str]) -> None:
    stdlib_path = Path(os.environ["AAA_STDLIB_PATH"])
    with capsys.disabled():
        print()
        exit_code = TestRunner(stdlib_path).run()

    assert exit_code == 0

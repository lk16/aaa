import os
from pathlib import Path

from aaa.run_tests import TestRunner


def test_stdlib() -> None:
    stdlib_path = Path(os.environ["AAA_STDLIB_PATH"])

    exit_code = TestRunner(stdlib_path).run()
    assert exit_code == 0

import os
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Tuple

import pytest

from aaa.run import Runner

if __name__ == "__main__":
    if "AAA_TESTS_CONTAINER" not in os.environ:
        print("Tests should only be run in test container!", file=sys.stderr)
        exit(1)

    pytest.main(["-vv", "--color=yes", __file__])


def run(source: str) -> Tuple[str, str, int]:
    binary_path = Path(NamedTemporaryFile(delete=False).name)
    source_path = Path(__file__).parent / "src" / source

    runner = Runner(source_path, None, False)
    exit_code = runner.run(None, True, binary_path, False)
    assert 0 == exit_code

    process = subprocess.run([str(binary_path)], capture_output=True)

    stdout = process.stdout.decode("utf-8")
    stderr = process.stderr.decode("utf-8")
    return stdout, stderr, process.returncode


@pytest.mark.parametrize(
    ["source", "expected_stdout", "expected_stderr", "expected_exitcode"],
    [
        pytest.param("assert_true.aaa", "", "", 0, id="true"),
        pytest.param("assert_false.aaa", "", "Assertion failure!\n", -6, id="false"),
    ],
)
def test_assert(
    source: str, expected_stdout: str, expected_stderr: str, expected_exitcode: int
) -> None:
    stdout, stderr, exit_code = run(source)
    assert expected_stdout == stdout
    assert expected_stderr == stderr
    assert expected_exitcode == exit_code

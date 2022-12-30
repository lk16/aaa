import os
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import time
from typing import Tuple

import pytest

from aaa.run import Runner

if __name__ == "__main__":
    if "AAA_TESTS_CONTAINER" not in os.environ:
        print("Tests should only be run in test container!", file=sys.stderr)
        exit(1)

    pytest.main(["-vv", "--color=yes", __file__])


def run(source: str, skip_valgrind: bool = False) -> Tuple[str, str, int]:
    binary = NamedTemporaryFile(delete=False).name
    source_path = Path(__file__).parent / "src" / source

    runner = Runner(source_path, None, False)
    exit_code = runner.run(None, True, binary, False)
    assert 0 == exit_code

    process = subprocess.run([binary], capture_output=True, timeout=2)

    stdout = process.stdout.decode("utf-8")
    stderr = process.stderr.decode("utf-8")
    exit_code = process.returncode

    if exit_code == 0 and not skip_valgrind:
        command = ["valgrind", "--error-exitcode=1", "--leak-check=full", binary]
        process = subprocess.run(command, capture_output=True, timeout=2)

        if process.returncode != 0:
            print(process.stdout.decode())
            print(process.stderr.decode(), file=sys.stderr)
            assert False, "Valgrind found memory errors"

    return stdout, stderr, exit_code


@pytest.mark.parametrize(
    ["source", "expected_stderr", "expected_exitcode"],
    [
        pytest.param("assert_true.aaa", "", 0, id="true"),
        pytest.param("assert_false.aaa", "Assertion failure!\n", -6, id="false"),
    ],
)
def test_assert(source: str, expected_stderr: str, expected_exitcode: int) -> None:
    stdout, stderr, exit_code = run(source)
    assert "" == stdout
    assert expected_stderr == stderr
    assert expected_exitcode == exit_code


@pytest.mark.parametrize(
    ["source", "expected_exitcode"],
    [pytest.param("exit_0.aaa", 0, id="0"), pytest.param("exit_1.aaa", 1, id="1")],
)
def test_exit(source: str, expected_exitcode: int) -> None:
    stdout, stderr, exit_code = run(source)
    assert "" == stdout
    assert "" == stderr
    assert expected_exitcode == exit_code


def test_time() -> None:
    stdout, stderr, exit_code = run("time.aaa")

    printed_time = int(stdout.strip())
    current_time = int(time())

    assert current_time - printed_time in [0, 1]
    assert "" == stderr
    assert 0 == exit_code


def test_gettimeofday() -> None:
    stdout, stderr, exit_code = run("gettimeofday.aaa")

    printed = stdout.strip().split()
    printed_usec = int(printed[0])
    printed_sec = int(printed[1])

    current_time = int(time())
    assert current_time - printed_sec in [0, 1]
    assert printed_usec in range(1_000_000)

    assert "" == stderr
    assert 0 == exit_code


def test_getcwd() -> None:
    stdout, stderr, exit_code = run("getcwd.aaa")
    assert "/app\n" == stdout
    assert "" == stderr
    assert 0 == exit_code


@pytest.mark.parametrize(
    ["source", "expected_stdout"],
    [
        pytest.param("chdir_ok.aaa", "/tmp\n", id="ok"),
        pytest.param("chdir_fail.aaa", "/app\n", id="fail"),
    ],
)
def test_chdir(source: str, expected_stdout: str) -> None:
    stdout, stderr, exit_code = run(source)
    assert expected_stdout == stdout
    assert "" == stderr
    assert 0 == exit_code


@pytest.mark.parametrize(
    ["source", "expected_stdout", "skip_valgrind"],
    [
        pytest.param("execve_ok.aaa", "", True, id="ok"),
        pytest.param("execve_fail.aaa", "", False, id="fail"),
    ],
)
def test_execve(source: str, expected_stdout: str, skip_valgrind: bool) -> None:
    stdout, stderr, exit_code = run(source, skip_valgrind)
    assert expected_stdout == stdout
    assert "" == stderr
    assert 0 == exit_code


# TODO add test for execve
# TODO add test for fork
# TODO add test for waitpid

# TODO add test for getpid
# TODO add test for getppid

# TODO add test for environ
# TODO add test for getenv
# TODO add test for setenv
# TODO add test for unsetenv

# TODO add test for open
# TODO add test for read
# TODO add test for write
# TODO add test for close

# TODO add test for socket
# TODO add test for bind
# TODO add test for listen
# TODO add test for accept

# TODO add test for connect

# TODO add test for fsync

# TODO add test for unlink

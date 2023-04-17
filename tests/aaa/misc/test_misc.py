import json
import os
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import time
from typing import Dict, Optional, Tuple

import pytest

from aaa.run import Runner


def compile(source: str) -> str:
    binary = NamedTemporaryFile(delete=False).name
    source_path = Path(__file__).parent / "src" / source

    runner = Runner(source_path, None, False)
    exit_code = runner.run(True, binary, False)
    assert 0 == exit_code
    return binary


def run(binary: str, env: Optional[Dict[str, str]] = None) -> Tuple[str, str, int]:
    process = subprocess.run([binary], capture_output=True, timeout=2, env=env)

    stdout = process.stdout.decode("utf-8")
    stderr = process.stderr.decode("utf-8")
    exit_code = process.returncode

    return stdout, stderr, exit_code


def compile_run(source: str) -> Tuple[str, str, int]:
    binary = compile(source)
    return run(binary)


@pytest.mark.parametrize(
    ["source", "expected_stderr", "expected_exitcode"],
    [
        pytest.param("assert_true.aaa", "", 0, id="true"),
        pytest.param("assert_false.aaa", "Assertion failure!\n", 1, id="false"),
    ],
)
def test_assert(source: str, expected_stderr: str, expected_exitcode: int) -> None:
    stdout, stderr, exit_code = compile_run(source)
    assert "" == stdout
    assert expected_stderr == stderr
    assert expected_exitcode == exit_code


@pytest.mark.parametrize(
    ["source", "expected_exitcode"],
    [pytest.param("exit_0.aaa", 0, id="0"), pytest.param("exit_1.aaa", 1, id="1")],
)
def test_exit(source: str, expected_exitcode: int) -> None:
    stdout, stderr, exit_code = compile_run(source)
    assert "" == stdout
    assert "" == stderr
    assert expected_exitcode == exit_code


def test_time() -> None:
    stdout, stderr, exit_code = compile_run("time.aaa")

    printed = stdout.strip().split()
    printed_usec = int(printed[1])
    printed_sec = int(printed[0])

    current_time = int(time())
    assert current_time - printed_sec in [0, 1]
    assert printed_usec in range(1_000_000)

    assert "" == stderr
    assert 0 == exit_code


def test_getcwd() -> None:
    stdout, stderr, exit_code = compile_run("getcwd.aaa")
    assert f"{os.getcwd()}\n" == stdout
    assert "" == stderr
    assert 0 == exit_code


@pytest.mark.parametrize(
    ["source", "expected_stdout"],
    [
        pytest.param("chdir_ok.aaa", "/tmp\n", id="ok"),
        pytest.param("chdir_fail.aaa", f"{os.getcwd()}\n", id="fail"),
    ],
)
def test_chdir(source: str, expected_stdout: str) -> None:
    stdout, stderr, exit_code = compile_run(source)
    assert expected_stdout == stdout
    assert "" == stderr
    assert 0 == exit_code


@pytest.mark.parametrize(
    ["source", "expected_stdout"],
    [
        pytest.param("execve_ok.aaa", "", id="ok"),
        pytest.param("execve_fail.aaa", "", id="fail"),
    ],
)
def test_execve(source: str, expected_stdout: str) -> None:
    stdout, stderr, exit_code = compile_run(source)
    assert expected_stdout == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_fork() -> None:
    stdout, stderr, exit_code = compile_run("fork.aaa")
    assert stdout in ["parent\nchild\n", "child\nparent\n"]
    assert "" == stderr
    assert 0 == exit_code


@pytest.mark.parametrize(
    ["source"],
    [
        pytest.param("waitpid_ok.aaa", id="ok"),
        pytest.param("waitpid_fail.aaa", id="fail"),
    ],
)
def test_waitpid(source: str) -> None:
    stdout, stderr, exit_code = compile_run(source)
    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_getpid() -> None:
    stdout, stderr, exit_code = compile_run("getpid.aaa")
    int(stdout.strip())
    assert "" == stderr
    assert 0 == exit_code


def test_getppid() -> None:
    stdout, stderr, exit_code = compile_run("getppid.aaa")

    assert f"{os.getpid()}\n" == stdout
    assert "" == stderr
    assert 0 == exit_code


DUMMY_ENV_VARS = {
    "KEY": "VALUE",
    "WITH_EQUALS_CHAR": "FOO=BAR",
}


def test_environ() -> None:
    binary = compile("environ.aaa")
    stdout, stderr, exit_code = run(binary, env=DUMMY_ENV_VARS)

    # NOTE: loading this output as json is a hack and may break in the future
    assert DUMMY_ENV_VARS == json.loads(stdout)
    assert "" == stderr
    assert 0 == exit_code


@pytest.mark.parametrize(
    ["source"],
    [
        pytest.param("getenv_ok.aaa", id="ok"),
        pytest.param("getenv_fail.aaa", id="fail"),
    ],
)
def test_getenv(source: str) -> None:
    binary = compile(source)
    stdout, stderr, exit_code = run(binary, env=DUMMY_ENV_VARS)
    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_setenv() -> None:
    binary = compile("setenv.aaa")
    stdout, stderr, exit_code = run(binary, env={})
    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_unsetenv() -> None:
    binary = compile("unsetenv.aaa")
    stdout, stderr, exit_code = run(binary, env=DUMMY_ENV_VARS)
    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


@pytest.mark.parametrize(
    ["source", "success"],
    [
        pytest.param("unlink_ok.aaa", True, id="ok"),
        pytest.param("unlink_fail.aaa", False, id="fail"),
    ],
)
def test_unlink(source: str, success: bool) -> None:

    dummy_file = Path("/tmp/unlink_dummy")

    if success:
        dummy_file.touch()

    stdout, stderr, exit_code = compile_run(source)

    if success:
        assert not dummy_file.exists()

    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_foreach_vector() -> None:
    stdout, stderr, exit_code = compile_run("foreach_vector.aaa")
    assert "2\n4\n6\n8\n" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_foreach_vector_empty() -> None:
    stdout, stderr, exit_code = compile_run("foreach_vector_empty.aaa")
    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_foreach_map() -> None:
    stdout, stderr, exit_code = compile_run("foreach_map.aaa")

    lines = set(stdout.strip().split("\n"))
    expected_lines = {"2 -> two", "4 -> four", "6 -> six", "8 -> eight"}

    assert expected_lines == lines
    assert "" == stderr
    assert 0 == exit_code


def test_foreach_map_empty() -> None:
    stdout, stderr, exit_code = compile_run("foreach_map_empty.aaa")
    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_foreach_custom() -> None:
    stdout, stderr, exit_code = compile_run("foreach_custom.aaa")
    assert "1\n2\n3\n4\n" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_foreach_set() -> None:
    stdout, stderr, exit_code = compile_run("foreach_set.aaa")

    lines = set(stdout.strip().split("\n"))
    expected_lines = {"2", "4", "6", "8"}

    assert expected_lines == lines
    assert "" == stderr
    assert 0 == exit_code


def test_assignment() -> None:
    stdout, stderr, exit_code = compile_run("assignment.aaa")
    assert '1\ntrue\nbar\n[2]\n{"two": 2}\n{2}\n6\n' == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_const() -> None:
    stdout, stderr, exit_code = compile_run("const.aaa")
    assert "69\n[5]\n[5]\n[5]\n[]\n" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_main_with_exit_code() -> None:
    stdout, stderr, exit_code = compile_run("main_with_exitcode.aaa")
    assert "" == stdout
    assert "" == stderr
    assert 1 == exit_code


def test_main_with_argv() -> None:
    binary_path = compile("main_with_argv.aaa")
    stdout, stderr, exit_code = run(binary_path)
    assert f'["{binary_path}"]\n' == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_return() -> None:
    stdout, stderr, exit_code = compile_run("return.aaa")
    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_enum() -> None:
    stdout, stderr, exit_code = compile_run("enum.aaa")
    assert "quit\n" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_recursion() -> None:
    stdout, stderr, exit_code = compile_run("recursion.aaa")

    expected_output = (
        '(struct s)<{"a": [(struct s)<{"a": []}>]}>\n'
        + "(enum json discriminant=0)<(struct empty)<{}>>\n"
        + "(enum json discriminant=4)<[(enum json discriminant=2)<5>]>\n"
        + '(enum json discriminant=5)<{"key": (enum json discriminant=1)<false>}>\n'
    )

    assert expected_output == stdout
    assert "" == stderr
    assert 0 == exit_code

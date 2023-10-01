import json
import os
import re
from pathlib import Path
from time import time

import pytest

from tests.aaa import compile, compile_run, run

SOURCE_PREFIX = Path(__file__).parent / "src"


def test_assert_true() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "assert_true.aaa")
    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_assert_false() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "assert_false.aaa")
    assert "" == stdout

    project_root = str(Path(__file__).parents[3])
    assert (
        f"Assertion failure at {project_root}/tests/aaa/misc/src/assert_false.aaa:2:11\n"
        == stderr
    )
    assert 1 == exit_code


@pytest.mark.parametrize(
    ["source", "expected_exitcode"],
    [pytest.param("exit_0.aaa", 0, id="0"), pytest.param("exit_1.aaa", 1, id="1")],
)
def test_exit(source: str, expected_exitcode: int) -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / source)
    assert "" == stdout
    assert "" == stderr
    assert expected_exitcode == exit_code


def test_time() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "time.aaa")

    printed = stdout.strip().split()
    printed_usec = int(printed[1])
    printed_sec = int(printed[0])

    current_time = int(time())
    assert current_time - printed_sec in [0, 1]
    assert printed_usec in range(1_000_000)

    assert "" == stderr
    assert 0 == exit_code


def test_getcwd() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "getcwd.aaa")
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
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / source)
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
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / source)
    assert expected_stdout == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_fork() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "fork.aaa")
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
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / source)
    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_getpid() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "getpid.aaa")
    int(stdout.strip())
    assert "" == stderr
    assert 0 == exit_code


def test_getppid() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "getppid.aaa")

    assert f"{os.getpid()}\n" == stdout
    assert "" == stderr
    assert 0 == exit_code


DUMMY_ENV_VARS = {
    "KEY": "VALUE",
    "WITH_EQUALS_CHAR": "FOO=BAR",
}


def test_environ() -> None:
    binary = compile(SOURCE_PREFIX / "environ.aaa")
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
    binary = compile(SOURCE_PREFIX / source)
    stdout, stderr, exit_code = run(binary, env=DUMMY_ENV_VARS)
    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_setenv() -> None:
    binary = compile(SOURCE_PREFIX / "setenv.aaa")
    stdout, stderr, exit_code = run(binary, env={})
    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_unsetenv() -> None:
    binary = compile(SOURCE_PREFIX / "unsetenv.aaa")
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

    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / source)

    if success:
        assert not dummy_file.exists()

    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_foreach_vector() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "foreach_vector.aaa")
    assert "2\n4\n6\n8\n" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_foreach_vector_empty() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "foreach_vector_empty.aaa")
    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_foreach_map() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "foreach_map.aaa")

    lines = set(stdout.strip().split("\n"))
    expected_lines = {"2 -> two", "4 -> four", "6 -> six", "8 -> eight"}

    assert expected_lines == lines
    assert "" == stderr
    assert 0 == exit_code


def test_foreach_map_empty() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "foreach_map_empty.aaa")
    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_foreach_custom() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "foreach_custom.aaa")
    assert "1\n2\n3\n4\n" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_foreach_set() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "foreach_set.aaa")

    lines = set(stdout.strip().split("\n"))
    expected_lines = {"2", "4", "6", "8"}

    assert expected_lines == lines
    assert "" == stderr
    assert 0 == exit_code


def test_assignment() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "assignment.aaa")
    assert '1\ntrue\nbar\n[2]\n{"two": 2}\n{2}\n6\n' == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_const() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "const.aaa")
    assert "69\n[5]\n[5]\n[5]\n[]\n" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_main_with_exit_code() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "main_with_exitcode.aaa")
    assert "" == stdout
    assert "" == stderr
    assert 1 == exit_code


def test_main_with_argv() -> None:
    binary_path = compile(SOURCE_PREFIX / "main_with_argv.aaa")
    stdout, stderr, exit_code = run(binary_path)
    assert f'["{binary_path}"]\n' == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_return() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "return.aaa")
    assert "" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_enum() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "enum.aaa")

    expected_stdout = (
        "Foo:bool_{false}\n"
        + "bool_ false\n"
        + "\n"
        + "Foo:bool_{true}\n"
        + "bool_ true\n"
        + "\n"
        + "Foo:int_{69}\n"
        + "int_ 69\n"
        + "\n"
        + 'Foo:str_{"hello"}\n'
        + "str_ hello\n"
        + "\n"
        + "Foo:vec_{[]}\n"
        + "vec_ []\n"
        + "\n"
        + "Foo:map_{{}}\n"
        + "map_ {}\n"
        + "\n"
        + "Foo:set_{{}}\n"
        + "set_ {}\n"
        + "\n"
        + "Foo:regex_{regex}\n"
        + "regex_ regex\n"
        + "\n"
        + "Foo:enum_{Foo:bool_{false}}\n"
        + "enum_ Foo:bool_{false}\n"
        + "\n"
        + "Foo:struct_{Bar{value: 0}}\n"
        + "struct_ Bar{value: 0}\n"
        + "\n"
        + "Foo:no_data{}\n"
        + "no_data \n"
        + "\n"
        + "Foo:multiple_data{3, []}\n"
        + "multiple_data [] 3\n"
        + "\n"
        + "Foo:bool_{true}\n"
        + "Foo:bool_{false}\n"
    )

    assert expected_stdout == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_recursion() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "recursion.aaa")

    expected_output = (
        "S{a: [S{a: []}]}\n"
        + "Json:null{Empty{}}\n"
        + "Json:array{[Json:integer{5}]}\n"
        + 'Json:object{{"key": Json:boolean{false}}}\n'
    )

    assert expected_output == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_todo() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "todo.aaa")

    assert "" == stdout
    assert stderr.startswith("Code at ")
    assert stderr.endswith(" is not implemented\n")
    assert 1 == exit_code


def test_unreachable() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "unreachable.aaa")

    assert "" == stdout
    assert stderr.startswith("Code at ")
    assert stderr.endswith(" should be unreachable\n")
    assert 1 == exit_code


def test_enum_without_associated_data() -> None:
    stdout, stderr, exit_code = compile_run(
        SOURCE_PREFIX / "enum_without_associated_data.aaa"
    )

    assert "some\nnone\n" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_enum_with_multiple_associated_fields() -> None:
    stdout, stderr, exit_code = compile_run(
        SOURCE_PREFIX / "enum_with_multiple_associated_fields.aaa"
    )

    assert (
        "quit\nmessage text=hello\nmessage_with_brackets text=world\nclick x=6 y=9\n"
        == stdout
    )
    assert "" == stderr
    assert 0 == exit_code


def test_enum_case_as() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "enum_case_as.aaa")

    assert "quit\ntext = hello\nx = 6 y = 9\n" == stdout
    assert "" == stderr
    assert 0 == exit_code


def test_struct() -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / "struct.aaa")

    expected_output = (
        "  bool_ = true\n"
        + "   int_ = 69\n"
        + "   str_ = hello world\n"
        + '   vec_ = ["foo"]\n'
        + '   map_ = {"3": "three"}\n'
        + '   set_ = {"hello"}\n'
        + " regex_ = regex\n"
        + "  enum_ = OptionalInt:some{3}\n"
        + "struct_ = Bar{value: 123}\n"
        + 'Foo{bool_: true, int_: 69, str_: "hello world", vec_: ["foo"], map_: {"3": "three"}, set_: {"hello"}, regex_: regex, enum_: OptionalInt:some{3}, struct_: Bar{value: 123}}\n'
        + 'Foo{bool_: false, int_: 0, str_: "", vec_: [], map_: {}, set_: {}, regex_: regex, enum_: OptionalInt:none{}, struct_: Bar{value: 0}}\n'
    )

    expected_output = re.sub("UserStruct[0-9a-f]+", "UserStructXYZ", expected_output)
    stdout = re.sub("UserStruct[0-9a-f]+", "UserStructXYZ", stdout)

    assert expected_output == stdout
    assert "" == stderr
    assert 0 == exit_code

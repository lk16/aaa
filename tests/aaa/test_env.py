from contextlib import redirect_stdout
from copy import copy
from io import StringIO
from unittest.mock import patch

import pytest

from aaa.run import Runner

TEST_ENV_VARS = {
    "USER": "lk16",
    "HOME": "/home/lk16",
}


def test_environ() -> None:
    runner = Runner.without_file("fn main { environ . }")

    with patch("lang.runtime.simulator.os.environ", TEST_ENV_VARS):
        with redirect_stdout(StringIO()) as stdout:
            runner.run()

    assert stdout.getvalue() in [
        '{"USER": "lk16", "HOME": "/home/lk16"}',
        '{"HOME": "/home/lk16", "USER": "lk16"}',
    ]


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        pytest.param('fn main { "USER" getenv . " " . . }', "true lk16", id="found"),
        pytest.param('fn main { "FOO" getenv . " " . . }', "false ", id="missing"),
    ],
)
def test_getenv(code: str, expected_output: str) -> None:
    runner = Runner.without_file(code)

    with patch("lang.runtime.simulator.os.environ", TEST_ENV_VARS):
        with redirect_stdout(StringIO()) as stdout:
            runner.run()

    assert stdout.getvalue() == expected_output


def test_setenv() -> None:
    runner = Runner.without_file('fn main { "ENV_VAR_NAME" "ENV_VAR_VALUE" setenv }')

    env_vars = copy(TEST_ENV_VARS)

    with patch("lang.runtime.simulator.os.environ", env_vars):
        with redirect_stdout(StringIO()) as stdout:
            runner.run()

    assert stdout.getvalue() == ""

    assert env_vars == {
        "ENV_VAR_NAME": "ENV_VAR_VALUE",
        **TEST_ENV_VARS,
    }


def test_unsetenv() -> None:
    runner = Runner.without_file('fn main { "HOME" unsetenv }')

    env_vars = copy(TEST_ENV_VARS)

    with patch("lang.runtime.simulator.os.environ", env_vars):
        with redirect_stdout(StringIO()) as stdout:
            runner.run()

    assert stdout.getvalue() == ""

    assert env_vars == {
        "USER": "lk16",
    }

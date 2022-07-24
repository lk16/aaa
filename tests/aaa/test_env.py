from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import pytest

from lang.runtime.program import Program
from lang.runtime.simulator import Simulator

TEST_ENV_VARS = {
    "USER": "lk16",
    "HOME": "/home/lk16",
}


def test_environ() -> None:
    program = Program.without_file("fn main { environ . }")

    with patch("lang.runtime.simulator.os.environ", TEST_ENV_VARS):
        with redirect_stdout(StringIO()) as stdout:
            Simulator(program).run()

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
    program = Program.without_file(code)

    with patch("lang.runtime.simulator.os.environ", TEST_ENV_VARS):
        with redirect_stdout(StringIO()) as stdout:
            Simulator(program).run()

    assert stdout.getvalue() == expected_output

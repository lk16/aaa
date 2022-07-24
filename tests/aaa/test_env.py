from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

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

from unittest.mock import patch

import pytest

from tests.aaa import check_aaa_main

DUMMY_UNIX_TIMESTAMP = 123456789


@pytest.mark.parametrize(
    ["code", "expected_output"],
    [
        pytest.param('"/home/lk16" chdir .', "true", id="ok"),
        pytest.param('"/non-existent" chdir .', "false", id="fail"),
    ],
)
def test_chdir(code: str, expected_output: str) -> None:
    def mock_chdir(path: str) -> None:
        if path == "/home/lk16":
            return

        if path == "/non-existent":
            raise OSError

        # We should never reach this
        raise NotImplementedError

    with patch("aaa.simulator.simulator.os.chdir", mock_chdir):
        check_aaa_main(code, expected_output, [])

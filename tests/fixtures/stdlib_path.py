import os
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest

from aaa.runner.runner import Runner


@pytest.fixture(autouse=True, scope="session")
def setup_test_environment() -> Generator[None, None, None]:
    stdlib_path = Path(os.environ["AAA_STDLIB_PATH"]) / "builtins.aaa"
    with patch.object(Runner, "_get_stdlib_path", return_value=stdlib_path):
        yield

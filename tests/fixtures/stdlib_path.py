import os
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True, scope="session")
def setup_test_environment() -> Generator[None, None, None]:
    stdlib_path = Path(os.environ["AAA_STDLIB_PATH"]) / "builtins.aaa"
    with patch("aaa.get_stdlib_path", return_value=stdlib_path):
        yield

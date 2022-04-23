import os
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True, scope="session")
def setup_test_environment() -> Generator[None, None, None]:
    env_vars = {
        "AAA_STDLIB_PATH": str(Path.cwd() / "stdlib"),
    }

    with patch.dict(os.environ, env_vars):
        yield

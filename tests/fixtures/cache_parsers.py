from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest

from aaa.parser.parser import Parser


@pytest.fixture(autouse=True, scope="session")
def cache_builtins_parser() -> Generator[None, None, None]:
    builtins_parser = Parser(Path("."), Path("."))._get_builtins_parser()

    with patch.object(Parser, "_get_builtins_parser", return_value=builtins_parser):
        yield


@pytest.fixture(autouse=True, scope="session")
def cache_source_parser() -> Generator[None, None, None]:
    builtins_parser = Parser(Path("."), Path("."))._get_source_parser()

    with patch.object(Parser, "_get_source_parser", return_value=builtins_parser):
        yield

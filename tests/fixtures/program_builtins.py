from typing import Any, Generator, List, Tuple
from unittest.mock import patch

import pytest
from _pytest.fixtures import SubRequest

from lang.exceptions import AaaLoadException
from lang.runtime.program import Builtins, Program


@pytest.fixture(scope="module", autouse=True)
def cache_program_builtins(request: SubRequest) -> Generator[None, None, None]:
    """
    Prevents that every test that runs Aaa code loads the builtins file.
    It just speeds up tests.
    """

    if "no_builtins_cache" in request.keywords:
        # Allow tests for broken builtin files to still function
        yield
        return

    program = Program.without_file("fn main { nop }")

    def cached_builtins(
        *args: Any,
        **kwargs: Any,
    ) -> Tuple[Builtins, List[AaaLoadException]]:
        return program._builtins, program.file_load_errors

    with patch.object(Program, "_load_builtins", cached_builtins):
        yield

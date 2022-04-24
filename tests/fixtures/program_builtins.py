from typing import Any, Generator, List, Tuple
from unittest.mock import patch

import pytest
from _pytest.fixtures import SubRequest

from lang.runtime.program import Builtins, FileLoadException, Program


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

    program = Program.without_file("fn main begin nop end")

    def cached_builtins(
        *args: Any,
        **kwargs: Any,
    ) -> Tuple[Builtins, List[FileLoadException]]:
        return program._builtins, program.file_load_errors

    with patch.object(Program, "_load_builtins", cached_builtins):
        yield

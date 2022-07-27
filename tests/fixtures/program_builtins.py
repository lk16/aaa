from typing import Any, Generator, List, Optional, Tuple
from unittest.mock import patch

import pytest
from _pytest.fixtures import SubRequest

from lang.exceptions import AaaLoadException
from lang.runtime.program import Builtins, Program

cached_builtins: Optional[Builtins] = None


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

    # We can't use a package/session scope fixture without breaking tests.
    # We also can't use a fixture with smaller scope without lowing the tests down a lot.
    # So we cache it ourselves -.-
    global cached_builtins

    if not cached_builtins:
        program = Program.without_file("fn main { nop }")
        cached_builtins = program._builtins
        assert not program.file_load_errors

    def load_cached_builtins(
        *args: Any,
        **kwargs: Any,
    ) -> Tuple[Builtins, List[AaaLoadException]]:
        assert cached_builtins
        return cached_builtins, []

    with patch.object(Program, "_load_builtins", load_cached_builtins):
        yield

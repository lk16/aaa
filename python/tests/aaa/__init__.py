from collections.abc import Sequence
from pathlib import Path
from typing import Any

from aaa import AaaException
from aaa.runner.exceptions import AaaTranslationException
from aaa.runner.runner import Runner


def check_aaa_main(
    code: str,
    expected_output: str,
    expected_exception_types: list[type[Exception]],
) -> Sequence[AaaException]:
    code = "fn main {\n" + code + "\n}"
    return check_aaa_full_source(code, expected_output, expected_exception_types)


def check_aaa_full_source(
    code: str,
    expected_output: str,
    expected_exception_types: list[type[Exception]],
    **run_kwargs: Any,
) -> Sequence[AaaException]:
    files = {Path("main.aaa"): code}
    return check_aaa_full_source_multi_file(
        files, expected_output, expected_exception_types, **run_kwargs
    )


def check_aaa_full_source_multi_file(
    file_dict: dict[Path, str],
    expected_output: str,
    expected_exception_types: list[type[Exception]],
    **run_kwargs: Any,
) -> Sequence[AaaException]:
    entrypoint = Path("main.aaa")
    runner = Runner(entrypoint, file_dict)

    exception_types: list[type[AaaException]] = []

    # Make type-checker happy
    stdout = ""
    stderr = ""

    try:
        completed_process = runner._run_process(
            compile=True,
            binary_path=None,
            run=True,
            args=[],
            capture_output=True,
            runtime_type_checks=True,
            **run_kwargs,
        )
    except AaaTranslationException as e:
        exception_types = [type(exc) for exc in e.exceptions]
    else:
        stderr = completed_process.stderr.decode("utf-8")
        stdout = completed_process.stdout.decode("utf-8")

    exception_types = [type(exc) for exc in runner.exceptions]

    if exception_types != expected_exception_types:
        # If we reach this code, some test for Aaa code is broken.
        # We print some info useful for debugging.

        error = (
            "\n"
            + "Expected exception types: "
            + " ".join(exc_type.__name__ for exc_type in expected_exception_types)
            + "\n"
            + "     Got exception types: "
            + " ".join(exc_type.__name__ for exc_type in exception_types)
            + "\n"
        )

        if runner.exceptions:
            error += "\nException(s):\n"

            for exception in runner.exceptions:
                error += f"{exception}\n"

        raise AssertionError(error)

    if not expected_exception_types:
        assert expected_output == stdout
        assert stderr == ""

    return runner.exceptions

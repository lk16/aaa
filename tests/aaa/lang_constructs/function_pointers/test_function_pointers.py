from pathlib import Path

import pytest

from tests.aaa import compile_run

SOURCE_PREFIX = Path(__file__).parent / "src"


@pytest.mark.parametrize(
    ["source_path", "expected_stdout"],
    [
        ("basic.aaa", "69\n69\n69\n69\n"),
        ("in_enum.aaa", "69\n69\n69\n"),
        ("in_struct.aaa", "69\n"),
        ("in_vector.aaa", "69\n"),
        ("assignment.aaa", "69\n"),
        ("returned.aaa", "69\n"),
        ("to_builtins.aaa", "69\n69\n69\n"),
        ("never_returns.aaa", "does_not_return was called!\n"),
        ("to_enum_constructor.aaa", "69\n"),
        ("to_enum_associated.aaa", "69\n"),
        ("to_struct_associated.aaa", "69\n"),
        ("imported/main.aaa", "69\n69\n69\n"),
    ],
)
def test_test_function_pointer(source_path: Path, expected_stdout: str) -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / source_path)

    assert expected_stdout == stdout
    assert "" == stderr
    assert 0 == exit_code


@pytest.mark.parametrize(
    ["source_path"],
    [
        ("zero_value_in_enum.aaa",),
        ("zero_value_in_struct.aaa",),
        ("zero_value_on_stack.aaa",),
    ],
)
def test_zero_value(source_path: Path) -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / source_path)

    assert "" == stdout
    assert "Function pointer with zero-value was called.\n" == stderr
    assert 1 == exit_code


@pytest.mark.parametrize(
    ["source_path", "expected_stderr"],
    [
        ("to_todo.aaa", "Code at ??:??:?? is not implemented\n"),
        ("to_unreachable.aaa", "Code at ??:??:?? should be unreachable\n"),
        ("to_assert.aaa", "Assertion failure at ??:??:??\n"),
    ],
)
def test_print_calling_location(source_path: Path, expected_stderr: str) -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / source_path)

    assert "" == stdout
    assert expected_stderr == stderr
    assert 1 == exit_code

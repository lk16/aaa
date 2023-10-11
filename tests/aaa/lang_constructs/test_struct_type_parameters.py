from pathlib import Path

import pytest

from aaa.runner.runner import compile_run

SOURCE_PREFIX = Path(__file__).parent / "src/struct_type_parameters"


@pytest.mark.parametrize(
    ["source_path", "expected_stdout"],
    [
        (
            "pair.aaa",
            'Pair{a: 69, b: "hello"}\n'
            "a = 69\n"
            "b = hello\n"
            'Pair{a: 420, b: "world"}\n'
            "a = 420\n"
            "b = world\n",
        ),
        ("pair_partial.aaa", 'Pair{a: "foo", b: "hello"}\n'),
        ("tree.aaa", "Tree{children: [Tree{children: [], data: 4}], data: 5}\n"),
        ("make_tree_with_type_param.aaa", ""),
    ],
)
def test_struct_type_parameters(source_path: Path, expected_stdout: str) -> None:
    stdout, stderr, exit_code = compile_run(SOURCE_PREFIX / source_path)

    assert expected_stdout == stdout
    assert "" == stderr
    assert 0 == exit_code

from pathlib import Path
from typing import List

import pytest
from pytest import CaptureFixture

from aaa.run import Runner


def expected_fizzbuzz_output() -> str:
    fizzbuzz_table = {
        0: "fizzbuzz",
        3: "fizz",
        5: "buzz",
        6: "fizz",
        9: "fizz",
        10: "buzz",
        12: "fizz",
    }

    output: List[str] = []

    for i in range(1, 101):
        output.append(fizzbuzz_table.get(i % 15, str(i)))

    return "\n".join(output) + "\n"


EXPECTED_EXAMPLE_OUTPUT = {
    "examples/one_to_ten.aaa": "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n",
    "examples/print_number.aaa": "42\n",
    "examples/fizzbuzz.aaa": expected_fizzbuzz_output(),
    "examples/print_twice.aaa": "hello!\nhello!\n",
    "examples/function_demo.aaa": "a=1\nb=2\nc=3\n",
    "examples/typing_playground.aaa": "five = 5\n3 5 max = 5\n4 factorial = 24\n7 dup_twice = 777\n",
    "examples/renamed_import/main.aaa": "5",
}


@pytest.mark.parametrize(
    ["example_file_path", "expected_output"],
    [
        pytest.param(
            "examples/one_to_ten.aaa",
            "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n",
            id="one_to_ten.aaa",
        ),
        pytest.param("examples/print_number.aaa", "42\n", id="print_number.aaa"),
        pytest.param(
            "examples/fizzbuzz.aaa", expected_fizzbuzz_output(), id="fizzbuzz.aaa"
        ),
        pytest.param(
            "examples/print_twice.aaa", "hello!\nhello!\n", id="print_twice.aaa"
        ),
        pytest.param(
            "examples/function_demo.aaa", "a=1\nb=2\nc=3\n", id="function_demo.aaa"
        ),
        pytest.param(
            "examples/typing_playground.aaa",
            "five = 5\n3 5 max = 5\n4 factorial = 24\n7 dup_twice = 777\n",
            id="typing_playground.aaa",
        ),
        pytest.param(
            "examples/renamed_import/main.aaa", "5", id="renamed_import/main.aaa"
        ),
        pytest.param(
            "examples/struct.aaa",
            "x = 0\ny = 0\nx = 3\ny = 4\n7\nx,y = 3,4\nx,y = 0,0\n",
            id="struct.aaa",
        ),
    ],
)
def test_examples(
    example_file_path: Path, expected_output: str, capfd: CaptureFixture[str]
) -> None:
    Runner(Path(example_file_path)).run()
    stdout, stderr = capfd.readouterr()
    assert str(stderr) == ""
    assert str(stdout) == expected_output

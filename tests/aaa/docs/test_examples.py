import subprocess
from ipaddress import IPv4Address
from pathlib import Path
from typing import List

import pytest
import requests
from pytest import CaptureFixture

from aaa.runner.runner import Runner


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
    ["entrypoint", "expected_output"],
    [
        pytest.param(
            "examples/one_to_ten.aaa",
            "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n",
            id="one_to_ten.aaa",
        ),
        pytest.param(
            "examples/fizzbuzz.aaa", expected_fizzbuzz_output(), id="fizzbuzz.aaa"
        ),
        pytest.param(
            "examples/renamed_import/main.aaa", "5\n", id="renamed_import/main.aaa"
        ),
        pytest.param("examples/import/main.aaa", "5\n", id="renamed_import/main.aaa"),
    ],
)
def test_examples(
    entrypoint: Path, expected_output: str, capfd: CaptureFixture[str]
) -> None:
    runner = Runner(entrypoint)
    runner.run(
        compile=True, binary_path=None, run=True, args=[], runtime_type_checks=True
    )
    stdout, stderr = capfd.readouterr()
    assert str(stderr) == ""
    assert str(stdout) == expected_output


def test_http_server() -> None:
    entrypoint = Path("examples/http_server.aaa")
    runner = Runner(entrypoint)

    binary = "/tmp/aaa/test_http_server"

    exit_code = runner.run(
        compile=True,
        binary_path=Path(binary),
        run=False,
        args=[],
        runtime_type_checks=True,
    )
    assert exit_code == 0

    subproc = subprocess.Popen(binary, stdout=subprocess.PIPE)

    stdout = subproc.stdout
    assert stdout

    # Wait until webserver prints first line, indicating server is running
    first_line = stdout.readline().decode()
    assert "Webserver running at" in first_line

    try:
        r = requests.get("http://localhost:8080")
        assert r.status_code == 200
        assert r.json() == {"message": "Hello world!"}
        assert r.headers["Content-Type"] == "application/json"

        r = requests.get("http://localhost:8080/")
        assert r.status_code == 200
        assert r.json() == {"message": "Hello world!"}
        assert r.headers["Content-Type"] == "application/json"

        r = requests.get("http://localhost:8080/statuses/error")
        assert r.status_code == 500
        assert r.text == "Internal Server Error\n"

        r = requests.get("http://localhost:8080/statuses/bad-request")
        assert r.status_code == 400
        assert r.text == "Bad Request\n"

        r = requests.get("http://localhost:8080/foo")
        assert r.status_code == 404
        assert r.text == "Not Found\n"

    finally:
        subproc.terminate()
        subproc.wait()


def test_http_client(capfd: CaptureFixture[str]) -> None:
    entrypoint = Path("examples/http_client.aaa")
    runner = Runner(entrypoint)
    runner.run(
        compile=True, binary_path=None, run=True, args=[], runtime_type_checks=True
    )

    stdout, stderr = capfd.readouterr()
    stdout_lines = stdout.split("\r\n")

    assert stderr == ""
    assert stdout_lines[0] == "HTTP/1.1 200 OK"
    IPv4Address(stdout_lines[-1].strip())  # should not fail


@pytest.mark.skip()
def test_shell() -> None:
    raise NotImplementedError  # TODO #71 Implement test for examples/shell.aaa


@pytest.mark.skip()
def test_sudoku_solver() -> None:
    raise NotImplementedError  # TODO #72 Implement test for examples/sudoku_solver.aaa

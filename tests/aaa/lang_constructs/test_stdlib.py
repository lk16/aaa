import os
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir

from aaa.run import Runner
from aaa.run_tests import TestRunner


def test_stdlib_python() -> None:
    stdlib_path = Path(os.environ["AAA_STDLIB_PATH"])

    exit_code = TestRunner(stdlib_path).run()
    assert exit_code == 0


def test_stdlib_transpiling() -> None:
    stdlib_path = Path(os.environ["AAA_STDLIB_PATH"])

    test_runner = TestRunner(stdlib_path)
    main_test_code = test_runner.build_main_test_file()

    main_test_file = Path(gettempdir()) / NamedTemporaryFile(delete=False).name
    main_test_file.write_text(main_test_code)

    output_file = Path(gettempdir()) / NamedTemporaryFile(delete=False).name

    runner = Runner(main_test_file, test_runner.parsed_files)
    exit_code = runner.transpile(output_file, compile=False, run=False)

    assert exit_code == 0

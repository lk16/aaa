import os
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir

from aaa.run import Runner
from aaa.run_tests import TestRunner


def test_stdlib_transpiling() -> None:
    stdlib_path = Path(os.environ["AAA_STDLIB_PATH"])

    test_runner = TestRunner(stdlib_path, False)
    main_test_code = test_runner.build_main_test_file()

    main_test_file = Path(gettempdir()) / NamedTemporaryFile(delete=False).name
    main_test_file.write_text(main_test_code)

    runner = Runner(main_test_file, test_runner.parsed_files, False)
    exit_code = runner.run(None, True, None, True)

    assert exit_code == 0

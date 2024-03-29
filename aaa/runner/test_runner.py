import re
import sys
from glob import glob
from pathlib import Path

from aaa import AaaException
from aaa.parser.exceptions import AaaParserBaseException
from aaa.parser.models import Function, SourceFile
from aaa.parser.parser import AaaParser
from aaa.runner.runner import Runner


class TestRunner:
    # Tell pytest to ignore this class
    __test__ = False

    def __init__(self, tests_root: str) -> None:
        self.tests_root = Path(tests_root).resolve()
        self.exceptions: list[AaaException] = []
        self.parsed_files: dict[Path, SourceFile] = {}
        self.test_functions: list[Function] = []
        self.verbose = False

    @classmethod
    def test_command(
        cls,
        path: str,
        verbose: bool,
        binary: str | None,
        runtime_type_checks: bool,
    ) -> int:
        test_runner = TestRunner(path)
        test_runner.set_verbose(verbose)

        if binary:
            binary_path = Path(binary)
        else:
            binary_path = None

        return test_runner.run(
            compile=True,
            binary=binary_path,
            run=True,
            runtime_type_checks=runtime_type_checks,
        )

    def set_verbose(self, verbose: bool) -> None:
        self.verbose = verbose

    def run(
        self,
        compile: bool,
        binary: Path | None,
        run: bool,
        runtime_type_checks: bool,
    ) -> int:
        main_file_code = self._build_main_test_file()

        if self.exceptions:
            for exception in self.exceptions:
                print(str(exception), file=sys.stderr)

            print(f"Found {len(self.exceptions)} error(s).", file=sys.stderr)
            return 1

        runner = Runner.without_file(main_file_code)
        runner.add_parsed_files(self.parsed_files)
        runner.set_verbose(self.verbose)
        return runner.run(
            compile=compile,
            binary_path=binary,
            run=run,
            runtime_type_checks=runtime_type_checks,
            args=[],
        )

    def _get_parsed_test_files(self) -> dict[Path, SourceFile]:
        glob_paths = glob("**/test_*.aaa", root_dir=self.tests_root, recursive=True)
        test_files = {(self.tests_root / path).resolve() for path in glob_paths}

        parsed_files: dict[Path, SourceFile] = {}

        parser = AaaParser(self.verbose)

        for test_file in sorted(test_files):
            try:
                parsed_files[test_file] = parser.parse_file(test_file)
            except AaaParserBaseException as e:
                self.exceptions.append(e)

        return parsed_files

    def _get_test_functions(self) -> list[Function]:
        test_functions: list[Function] = []

        for parsed_file in self.parsed_files.values():
            for function in parsed_file.functions:
                if function.is_test():
                    test_functions.append(function)

        return test_functions

    def _get_test_func_alias(self, test_number: int) -> str:
        alias = str(test_number)

        # Replace digits with letters, because digits
        # can't be part of identifiers (such as aliases)
        for i in range(10):
            alias = alias.replace(str(i), chr(ord("a") + i))

        return f"test_{alias}"

    def _build_main_test_file(self) -> str:
        code = (Path(__file__).parent / "run_tests.aaa").read_text()

        self.parsed_files = self._get_parsed_test_files()
        self.test_functions = self._get_test_functions()

        imports: list[str] = []
        pushed_test_funcs: list[str] = []

        for test_number, test_function in enumerate(self.test_functions):
            from_ = str(test_function.position.file)
            func_name = test_function.get_func_name()

            # Functions are aliased to prevent naming collisions
            alias = self._get_test_func_alias(test_number)

            imports.append(f'from "{from_}" import {func_name} as {alias}')
            pushed_test_funcs.append(
                f'    "{alias}" fn "{from_}::{func_name}" push_test_function'
            )

        code = re.sub(" *// \\[COMMENT\\].*\n", "", code)
        code = re.sub(" *// \\[IMPORTS\\].*\n", "\n".join(imports) + "\n", code)
        code = re.sub(
            " *// \\[TEST FUNCTIONS\\].*\n",
            "\n".join(pushed_test_funcs) + "\n",
            code,
        )
        return code

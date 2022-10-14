import os
from glob import glob
from pathlib import Path
from typing import List, Set

from aaa.parser.models import Function, ParsedFile
from aaa.parser.parser import Parser
from aaa.run import Runner


class TestRunner:
    def __init__(self, path: Path) -> None:
        self.path = path

    def run(self) -> int:
        test_files = self._collect_test_files()
        parsed_files: List[ParsedFile] = []

        for test_file in test_files:
            parsed_files.append(self._parse_file(test_file))

        test_functions: List[Function] = []

        for parsed_file in parsed_files:
            for function in parsed_file.functions:
                if not function.struct_name and function.func_name.name.startswith(
                    "test_"
                ):
                    test_functions.append(function)

        main_file_code = self._build_main_test_file(test_functions)

        # TODO make sure test functions don't take any arguments and don't return any values

        return Runner.without_file(main_file_code).run()

    def _collect_test_files(self) -> Set[Path]:
        glob_paths = glob("**/test_*.aaa", root_dir=self.path, recursive=True)
        return {(self.path / path).resolve() for path in glob_paths}

    def _parse_file(self, file: Path) -> ParsedFile:
        # TODO move this out
        builtins_path = Path(os.environ["AAA_STDLIB_PATH"]) / "builtins.aaa"

        parser = Parser(file, builtins_path)

        # TODO handle parse errors gracefully
        parser_output = parser.run()

        return parser_output.parsed[file]

    def _build_main_test_file(self, test_functions: List[Function]) -> str:
        # TODO prevent naming collision (hash file name + function name)
        content = ""

        for test_function in test_functions:
            from_ = str(test_function.file)

            if from_.endswith(".aaa"):
                from_ = from_[: -len(".aaa")]

            func_name = test_function.func_name.name

            content += f'from "{from_}" import {func_name}\n'

        content += "\n"
        content += "fn main {\n"

        for test_function in test_functions:
            content += f"    {test_function.func_name.name}\n"

        content += "}\n"
        return content

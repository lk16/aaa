import os
from glob import glob
from pathlib import Path
from typing import Dict, List

from aaa.parser.models import Function, ParsedFile
from aaa.parser.parser import Parser
from aaa.run import Runner


class TestRunner:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.builtins_path = Path(os.environ["AAA_STDLIB_PATH"]) / "builtins.aaa"

    def run(self) -> int:
        parsed_files = self._get_parsed_test_files()
        test_functions = self._get_test_functions(parsed_files)
        main_file_code = self._build_main_test_file(test_functions)
        return Runner.without_file(main_file_code, parsed_files).run()

    def _get_parsed_test_files(self) -> Dict[Path, ParsedFile]:
        glob_paths = glob("**/test_*.aaa", root_dir=self.path, recursive=True)
        test_files = {(self.path / path).resolve() for path in glob_paths}

        return {
            test_file: self._parse_file(test_file) for test_file in sorted(test_files)
        }

    def _parse_file(self, file: Path) -> ParsedFile:
        parser = Parser(file, self.builtins_path)

        # TODO handle parse errors gracefully
        return parser._parse(file, parser._get_source_parser())

    def _get_test_functions(
        self, parsed_files: Dict[Path, ParsedFile]
    ) -> List[Function]:

        test_functions: List[Function] = []

        for parsed_file in parsed_files.values():
            for function in parsed_file.functions:
                if function.is_test():
                    test_functions.append(function)

        return test_functions

    def _build_main_test_file(self, test_functions: List[Function]) -> str:
        # TODO prevent naming collision (hash file name + function name)

        # TODO tests crash after first failing test
        imports = ""
        main_body = ""

        test_count = len(test_functions)

        for test_number, test_function in enumerate(test_functions, start=1):
            from_ = str(test_function.file)
            func_name = test_function.func_name.name
            imports += f'from "{from_}" import {func_name}\n'
            main_body += (
                f'     "[{test_number}/{test_count}] {from_}::{func_name}\\n" .\n'
            )
            main_body += f"     {func_name}\n"

        return imports + "\nfn main{\n" + main_body + "}\n"

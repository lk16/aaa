from pathlib import Path
from typing import Dict, List, Optional

from aaa import AaaRunnerException
from aaa.parser.exceptions import ParserBaseException
from aaa.parser.models import ParsedFile, ParserOutput
from aaa.parser.single_file_parser import SingleFileParser
from aaa.tokenizer.tokenizer import Tokenizer


class Parser:
    def __init__(
        self,
        entrypoint: Path,
        builtins_path: Path,
        parsed_files: Optional[Dict[Path, ParsedFile]],
        verbose: bool,
    ) -> None:
        self.entrypoint = entrypoint.resolve()
        self.builtins_path = builtins_path
        self.parsed: Dict[Path, ParsedFile] = parsed_files or {}
        self.parse_queue = [self.entrypoint]
        self.exceptions: List[ParserBaseException] = []
        self.verbose = verbose  # TODO use

    def run(self) -> ParserOutput:
        self.parsed[self.builtins_path] = self.parse(self.builtins_path, False)

        for file in self.parse_queue:
            try:
                self.parsed[file] = self.parse(file, True)
            except ParserBaseException as e:
                self.exceptions.append(e)
            else:
                self._enqueue_dependencies(self.parsed[file])

        if self.exceptions:
            raise AaaRunnerException(self.exceptions)

        return ParserOutput(
            parsed=self.parsed,
            builtins_path=self.builtins_path,
            entrypoint=self.entrypoint,
        )

    def parse(self, file: Path, is_regular_file: bool) -> ParsedFile:
        tokens = Tokenizer(file, self.verbose).run()
        parser = SingleFileParser(file, tokens, self.verbose)

        if is_regular_file:
            return parser.parse_regular_file()
        return parser.parse_builtins_file()

    def _enqueue_dependencies(self, parsed_file: ParsedFile) -> None:
        for dependency in parsed_file.dependencies():
            if dependency not in self.parsed:
                self.parse_queue.append(dependency)

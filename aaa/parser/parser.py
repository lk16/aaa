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
        parsed_files: Optional[Dict[Path, ParsedFile]] = None,
    ) -> None:
        self.entrypoint = entrypoint.resolve()
        self.builtins_path = builtins_path

        self.parsed: Dict[Path, ParsedFile] = parsed_files or {}
        self.parse_queue = [self.entrypoint]
        self.exceptions: List[ParserBaseException] = []

    def run(self) -> ParserOutput:
        self.parsed[self.builtins_path] = self._parse(self.builtins_path, False)

        for file in self.parse_queue:
            try:
                self.parsed[file] = self._parse(file, True)
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

    def _parse(self, file: Path, is_regular_file: bool) -> ParsedFile:
        tokens = Tokenizer(file).run()
        parser = SingleFileParser(file, tokens)

        if is_regular_file:
            return parser.parse_regular_file()
        return parser.parse_builtins_file()

    def _enqueue_dependencies(self, parsed_file: ParsedFile) -> None:
        for import_ in parsed_file.imports:
            if import_.source_file not in self.parsed:
                self.parse_queue.append(import_.source_file)

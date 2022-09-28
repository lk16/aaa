from pathlib import Path
from typing import Dict, List

from lark.exceptions import UnexpectedInput, VisitError
from lark.lark import Lark

from aaa.parser import aaa_builtins_parser, aaa_source_parser
from aaa.parser.exceptions import FileReadError, ParseException, ParserBaseException
from aaa.parser.models import ParsedFile, ParserOutput
from aaa.parser.transformer import AaaTransformer


class Parser:
    def __init__(self, entrypoint: Path, builtins_path: Path) -> None:
        self.entrypoint = entrypoint
        self.builtins_path = builtins_path

        self.parsed: Dict[Path, ParsedFile] = {}
        self.parse_queue = [self.entrypoint]
        self.exceptions: List[ParserBaseException] = []

    def run(self) -> ParserOutput:
        self.parsed[self.builtins_path] = self._parse(
            self.builtins_path, aaa_builtins_parser
        )

        for file in self.parse_queue:
            try:
                self.parsed[file] = self._parse(file, aaa_source_parser)
            except ParserBaseException as e:
                self.exceptions.append(e)
            else:
                self._enqueue_dependencies(file, self.parsed[file])

        return ParserOutput(
            parsed=self.parsed,
            builtins_path=self.builtins_path,
            entrypoint=self.entrypoint,
            exceptions=self.exceptions,
        )

    def _parse(self, file: Path, parser: Lark) -> ParsedFile:
        try:
            code = file.read_text()
        except OSError:
            raise FileReadError(file)

        try:
            tree = parser.parse(code)
        except UnexpectedInput as e:
            raise ParseException(file=file, parse_error=e)

        try:
            parsed_file = AaaTransformer(file).transform(tree)
        except VisitError as e:
            raise e.orig_exc

        assert isinstance(parsed_file, ParsedFile)
        return parsed_file

    def _enqueue_dependencies(self, file: Path, parsed_file: ParsedFile) -> None:
        for import_ in parsed_file.imports:
            dependency = (file.parent / f"{import_.source}.aaa").resolve()

            if dependency not in self.parsed:
                self.parse_queue.append(dependency)

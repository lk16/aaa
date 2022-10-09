from pathlib import Path
from typing import Dict, List

from lark.exceptions import UnexpectedInput, VisitError
from lark.lark import Lark

from aaa import AaaRunnerException
from aaa.parser.exceptions import FileReadError, ParseException, ParserBaseException
from aaa.parser.models import ParsedFile, ParserOutput
from aaa.parser.transformer import AaaTransformer


class Parser:
    def __init__(self, entrypoint: Path, builtins_path: Path) -> None:
        self.entrypoint = entrypoint.resolve()
        self.builtins_path = builtins_path

        self.parsed: Dict[Path, ParsedFile] = {}
        self.parse_queue = [self.entrypoint]
        self.exceptions: List[ParserBaseException] = []

    def run(self) -> ParserOutput:
        builtins_parser = self._get_builtins_parser()
        source_parser = self._get_source_parser()

        self.parsed[self.builtins_path] = self._parse(
            self.builtins_path, builtins_parser
        )

        for file in self.parse_queue:
            try:
                self.parsed[file] = self._parse(file, source_parser)
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

    def _enqueue_dependencies(self, parsed_file: ParsedFile) -> None:
        for import_ in parsed_file.imports:
            if import_.source_file not in self.parsed:
                self.parse_queue.append(import_.source_file)

    def _get_builtins_parser(self) -> Lark:
        grammar_path = Path(__file__).parent / "aaa.lark"

        return Lark(
            open(grammar_path).read(),
            start="builtins_file_root",
            maybe_placeholders=True,
            parser="lalr",
        )

    def _get_source_parser(self) -> Lark:
        grammar_path = Path(__file__).parent / "aaa.lark"

        return Lark(
            open(grammar_path).read(),
            start="regular_file_root",
            maybe_placeholders=True,
            parser="lalr",
        )

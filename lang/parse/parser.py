import os
from pathlib import Path
from typing import Dict

from lark.exceptions import UnexpectedInput, VisitError
from lark.lark import Lark

from lang.exceptions.misc import AaaParseException, MissingEnvironmentVariable
from lang.models.parse import ParsedFile
from lang.parse import aaa_builtins_parser, aaa_source_parser
from lang.parse.transformer import AaaTransformer


class Parser:
    def __init__(self, entrypoint: Path) -> None:
        self.entrypoint = entrypoint
        self.parsed: Dict[Path, ParsedFile] = {}
        self.parse_queue = [self.entrypoint]

    def run(self) -> Dict[Path, ParsedFile]:
        # TODO handle exceptions

        self._parse(self._get_builtins_path(), aaa_builtins_parser)

        for file in self.parse_queue:
            self._parse(file, aaa_source_parser)

        return self.parsed

    def _get_builtins_path(self) -> Path:
        try:
            stdlib_path = Path(os.environ["AAA_STDLIB_PATH"])
        except KeyError:
            raise MissingEnvironmentVariable("AAA_STDLIB_PATH")

        return stdlib_path / "builtins.aaa"

    def _parse(self, file: Path, parser: Lark) -> None:
        code = file.read_text()

        try:
            tree = parser.parse(code)
        except UnexpectedInput as e:
            raise AaaParseException(file=file, parse_error=e)

        try:
            parsed_file = AaaTransformer(file).transform(tree)
        except VisitError as e:
            raise e.orig_exc

        self.parsed[file] = parsed_file
        self._enqueue_dependencies(file, parsed_file)

    def _enqueue_dependencies(self, file: Path, parsed_file: ParsedFile) -> None:
        for import_ in parsed_file.imports:
            dependency = (file.parent / f"{import_.source}.aaa").resolve()

            if dependency not in self.parsed:
                self.parse_queue.append(dependency)

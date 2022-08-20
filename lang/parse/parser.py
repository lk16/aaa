import os
from pathlib import Path
from typing import Dict, Tuple

from lark.exceptions import UnexpectedInput, VisitError
from lark.lark import Lark

from lang.exceptions.misc import AaaParseException, MissingEnvironmentVariable
from lang.models.parse import ParsedBuiltinsFile, ParsedFile
from lang.parse import aaa_builtins_parser, aaa_source_parser
from lang.parse.transformer import AaaTransformer


class Parser:
    def __init__(self, entrypoint: Path) -> None:
        self.entrypoint = entrypoint
        self.parsed: Dict[Path, ParsedFile | ParsedBuiltinsFile] = {}
        self.parse_queue = [self.entrypoint]

    # TODO get rid of ParsedBuiltinsFile
    def run(self) -> Tuple[Dict[Path, ParsedFile], Dict[Path, ParsedBuiltinsFile]]:
        self._parse(self._get_builtins_path(), aaa_builtins_parser)

        for file in self.parse_queue:
            self._parse(file, aaa_source_parser)

        parsed_files: Dict[Path, ParsedFile] = {}
        parsed_builtin_files: Dict[Path, ParsedBuiltinsFile] = {}

        for file, parsed in self.parsed.items():
            if isinstance(parsed, ParsedFile):
                parsed_files[file] = parsed
            elif isinstance(parsed, ParsedBuiltinsFile):
                parsed_builtin_files[file] = parsed
            else:  # pragma: nocover
                assert False

        return parsed_files, parsed_builtin_files

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
            parsed_file: ParsedFile | ParsedBuiltinsFile = AaaTransformer(
                file
            ).transform(tree)
        except VisitError as e:
            raise e.orig_exc

        self.parsed[file] = parsed_file

        if isinstance(parsed_file, ParsedFile):
            self._enqueue_dependencies(file, parsed_file)

    def _enqueue_dependencies(self, file: Path, parsed_file: ParsedFile) -> None:
        for import_ in parsed_file.imports:
            dependency = (file.parent / f"{import_.source}.aaa").resolve()

            if dependency not in self.parsed:
                self.parse_queue.append(dependency)

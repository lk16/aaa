import sys
from parser.parser.exceptions import ParseError
from parser.tokenizer.exceptions import TokenizerError
from parser.tokenizer.models import Token
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional, Tuple

from lang.grammar.parser import parse as parse_aaa
from lang.runtime.parse import Function, ParsedFile
from lang.typing.checker import TypeChecker
from lang.typing.exceptions import FunctionNameCollision, TypeException

# Identifiable are things identified uniquely by a filepath and name
Identifiable = Function

FileLoadException = TokenizerError | ParseError | TypeException


class Program:
    def __init__(self, file: Path) -> None:
        self.entry_point_file = file.resolve()
        self.identifiers: Dict[Path, Dict[str, Identifiable]] = {}
        self.file_load_errors = self._load_file(self.entry_point_file)

    @classmethod
    def without_file(cls, code: str) -> "Program":
        with NamedTemporaryFile(delete=False) as file:
            saved_file = Path(file.name)
            saved_file.write_text(code)
            return cls(file=saved_file)

    def exit_on_error(self) -> None:  # pragma: nocover
        if not self.file_load_errors:
            return

        for error in self.file_load_errors:
            print(str(error), file=sys.stderr)
            if not str(error).endswith("\n"):
                print(file=sys.stderr)

        error_count = len(self.file_load_errors)
        print(f"Found {error_count} error{'' if error_count == 1 else 's'}.")
        exit(1)

    def _load_file(self, file: Path) -> List[FileLoadException]:
        try:
            tokens, parsed_file = self._parse_file(file)
        except (TokenizerError, ParseError) as e:
            return [e]

        try:
            self.identifiers[file] = self._load_file_identifiers(
                file, parsed_file, tokens
            )
        except TypeException as e:
            return [e]

        return self._type_check_file(file, parsed_file, tokens)

    def _parse_file(self, file: Path) -> Tuple[List[Token], ParsedFile]:
        code = file.read_text()
        tokens, tree = parse_aaa(str(file), code)
        parsed_file = ParsedFile.from_tree(tree, tokens, code)
        return tokens, parsed_file

    def _load_file_identifiers(
        self, file: Path, parsed_file: ParsedFile, tokens: List[Token]
    ) -> Dict[str, Identifiable]:
        identifiers: Dict[str, Identifiable] = {}

        for function in parsed_file.functions:
            if function.name in identifiers:
                raise FunctionNameCollision(file, function, tokens, function)
            identifiers[function.name] = function

        return identifiers

    def _type_check_file(
        self, file: Path, parsed_file: ParsedFile, tokens: List[Token]
    ) -> List[FileLoadException]:
        type_exceptions: List[FileLoadException] = []
        for function in parsed_file.functions:
            try:
                TypeChecker(file, function, tokens, self).check()
            except TypeException as e:
                type_exceptions.append(e)

        return type_exceptions

    def get_function(self, name: str) -> Optional[Function]:
        try:
            # TODO this won't always work when we support multiple files
            identified = self.identifiers[self.entry_point_file][name]
        except KeyError:
            return None

        # TODO check that identified is a Function when Identifiable becomes a union

        return identified

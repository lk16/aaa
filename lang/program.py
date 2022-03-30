import sys
from parser.tokenizer.models import Token
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional, Tuple

from lang.grammar.parser import parse as parse_aaa
from lang.parse import Function, ParsedFile
from lang.typing.checker import TypeChecker
from lang.typing.exceptions import FunctionNameCollision, TypeException

# Identifiable are things identified uniquely by a filepath and name
Identifiable = Function


class Program:
    def __init__(self, file: Path, exit_on_error: bool = True) -> None:
        self.exit_on_error = exit_on_error
        self.entry_point_file = file.resolve()
        self.identifiers: Dict[Path, Dict[str, Identifiable]] = {}
        self._load_file(self.entry_point_file)

    @classmethod
    def without_file(cls, code: str, exit_on_error: bool = True) -> "Program":
        with NamedTemporaryFile(delete=False) as file:
            saved_file = Path(file.name)
            saved_file.write_text(code)
            return cls(file=saved_file, exit_on_error=exit_on_error)

    def _load_file(self, file: Path) -> None:
        tokens, parsed_file = self._parse_file(file)

        try:
            self.identifiers[file] = self._load_file_identifiers(
                file, parsed_file, tokens
            )
            self._type_check_file(file, parsed_file, tokens)
        except TypeException as e:
            if self.exit_on_error:  # pragma: nocover
                print(e.what(), file=sys.stderr, end="")
                exit(1)  # TODO handle more gracefully
            raise e

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
    ) -> None:
        for function in parsed_file.functions:
            TypeChecker(file, function, tokens, self).check()

    def get_function(self, name: str) -> Optional[Function]:
        try:
            # TODO this won't always work when we support multiple files
            identified = self.identifiers[self.entry_point_file][name]
        except KeyError:
            return None

        # TODO check that identified is a Function when Identifiable becomes a union

        return identified

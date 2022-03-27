from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict

from lang.parse import Function, parse
from lang.typing.checker import TypeChecker
from lang.typing.exceptions import FunctionNameCollision, UnknownFunction

IdentifyType = Function


class Program:
    def __init__(self, file: Path) -> None:
        self.entry_point_file = file.resolve()
        self.identifiers: Dict[str, IdentifyType] = {}
        self._load_identifiers()

    @classmethod
    def without_file(cls, code: str) -> "Program":
        with NamedTemporaryFile() as file:
            saved_file = Path(file.name)
            saved_file.write_text(code)
            return cls(file=saved_file)

    def _load_identifiers(self) -> None:
        file = self.entry_point_file

        filename = str(file)
        code = file.read_text()
        parsed_file = parse(filename, code)

        identifiers: Dict[str, Function] = {}
        for function in parsed_file.functions:
            if function.name in identifiers:
                raise FunctionNameCollision

            identifiers[function.name] = function

        self.identifiers = identifiers
        TypeChecker(file, parsed_file, self).check()

    def get_function(self, name: str) -> Function:
        # TODO check for both KeyError
        try:
            identified = self.identifiers[name]
        except KeyError as e:
            raise UnknownFunction from e

        # TODO check that identified is a Function when multiple IdentifyType becomes a union

        return identified

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List

from lang.parse import Function, parse
from lang.typing.checker import TypeChecker
from lang.typing.exceptions import FunctionNameCollision

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
        identified = self.identifiers[name]

        if not isinstance(identified, Function):
            raise NotImplementedError

        return identified

    def get_functions(self) -> List[Function]:
        return [
            identified
            for identified in self.identifiers.values()
            if isinstance(identified, Function)
        ]

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict

from lang.parse import File, Function, parse
from lang.typing.checker import TypeChecker


class Program:
    @classmethod
    def without_file(cls, code: str) -> "Program":
        with NamedTemporaryFile() as file:
            saved_file = Path(file.name)
            saved_file.write_text(code)
            return cls(file=saved_file)

    def __init__(self, file: Path) -> None:
        self.entry_point_file = file.resolve()
        self.parsed_files: Dict[Path, File] = {}
        self._load_file(self.entry_point_file)

    def _load_file(self, file: Path) -> None:
        if file.resolve() in self.parsed_files:
            return

        filename = str(file.resolve())
        code = file.read_text()
        parsed_file = parse(filename, code)

        # TODO when import is implemented: load imported files here
        TypeChecker(file.resolve(), parsed_file, self).check()

        self.parsed_files[file.resolve()] = parsed_file

    def get_function(self, name: str) -> Function:
        return self.parsed_files[self.entry_point_file].functions[name]

import os
import sys
from pathlib import Path
from typing import Sequence

from aaa import AaaException
from aaa.cross_referencer.cross_referencer import CrossReferencer
from aaa.parser.parser import Parser
from aaa.type_checker.type_checker import TypeChecker


class Runner:
    def __init__(self, entrypoint: Path) -> None:
        self.entrypoint = entrypoint
        self.exceptions: Sequence[AaaException] = []

    def _print_exceptions(self) -> None:
        for exception in self.exceptions:
            print(str(exception), end="", file=sys.stderr)
            print()

        print(f"Found {len(self.exceptions)} errors.", file=sys.stderr)

    def run(self) -> int:
        try:
            stdlib_path = Path(os.environ["AAA_STDLIB_PATH"]) / "builtins.aaa"
        except KeyError:
            print("Environment variable AAA_STDLIB_PATH is not set.")
            print("Cannot find standard library!")
            return 1

        parser_output = Parser(self.entrypoint, stdlib_path).run()
        self.exceptions = parser_output.exceptions

        if self.exceptions:
            self._print_exceptions()
            return 1

        cross_referencer_output = CrossReferencer(parser_output).run()
        self.exceptions = cross_referencer_output.exceptions

        if self.exceptions:
            self._print_exceptions()
            return 1

        print("WARNING: TypeChecker is skipped")
        return 0

        type_checker_output = TypeChecker(cross_referencer_output).run()

        self.exceptions = type_checker_output.exceptions

        if self.exceptions:
            self._print_exceptions()
            return 1

        return 0

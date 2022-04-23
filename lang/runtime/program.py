import os
import sys
from dataclasses import dataclass
from parser.parser.exceptions import ParseError
from parser.tokenizer.exceptions import TokenizerError
from parser.tokenizer.models import Token
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional, Tuple

from lang.grammar.parser import parse as parse_aaa
from lang.instructions.generator import InstructionGenerator
from lang.instructions.types import Instruction
from lang.runtime.debug import format_str
from lang.runtime.parse import Function, ParsedBuiltinsFile, ParsedFile
from lang.typing.checker import TypeChecker
from lang.typing.exceptions import (
    AbsoluteImportError,
    CyclicImportError,
    FileReadError,
    FunctionNameCollision,
    ImportedItemNotFound,
    TypeException,
)


@dataclass(kw_only=True)
class ProgramImport:
    original_name: str
    source_file: Path


# Identifiable are things identified uniquely by a filepath and name
Identifiable = Function | ProgramImport

# TODO clean this union up once we have better baseclasses for exceptions
FileLoadException = (
    TokenizerError | ParseError | TypeException | FileReadError | CyclicImportError
)

# TODO use cli flag instead
PARSE_VERBOSE = "AAA_PARSING_DEBUG" in os.environ


class Program:
    def __init__(self, file: Path) -> None:
        self.entry_point_file = file.resolve()
        self.identifiers: Dict[Path, Dict[str, Identifiable]] = {}
        self.function_instructions: Dict[Path, Dict[str, List[Instruction]]] = {}

        # Used to detect cyclic import loops
        self.file_load_stack: List[Path] = []

        self.file_load_errors = self._load_builtins()

        if self.file_load_errors:
            return

        self.file_load_errors = self._load_file(self.entry_point_file)

    @classmethod
    def without_file(cls, code: str) -> "Program":
        with NamedTemporaryFile(delete=False) as file:
            saved_file = Path(file.name)
            saved_file.write_text(code)
            return cls(file=saved_file)

    def _load_builtins(self) -> List[FileLoadException]:
        try:
            stdlib_path = Path(os.environ["AAA_STDLIB_PATH"])
        except KeyError:
            raise NotImplementedError  # TODO

        if not stdlib_path.exists():
            raise NotImplementedError  # TODO

        builtins_file = stdlib_path / "builtins.aaa"

        try:
            tokens, parsed_file = self._parse_builtins_file(builtins_file)
        except (TokenizerError, ParseError) as e:
            return [e]
        except OSError:
            return [FileReadError(builtins_file)]

        raise NotImplementedError  # TODO

    def exit_on_error(self) -> None:  # pragma: nocover
        if not self.file_load_errors:
            return

        for error in self.file_load_errors:
            print(str(error), file=sys.stderr)
            if not str(error).endswith("\n"):
                print(file=sys.stderr)

        error_count = len(self.file_load_errors)
        maybe_s = "" if error_count == 1 else "s"
        print(f"Found {error_count} error{maybe_s}.", file=sys.stderr)
        exit(1)

    def _load_file(self, file: Path) -> List[FileLoadException]:
        # TODO make sure the file wasn't loaded already

        if file in self.file_load_stack:
            return [
                CyclicImportError(dependencies=self.file_load_stack, failed_import=file)
            ]

        self.file_load_stack.append(file)

        try:
            tokens, parsed_file = self._parse_regular_file(file)
        except (TokenizerError, ParseError) as e:
            self.file_load_stack.pop()
            return [e]
        except OSError:
            self.file_load_stack.pop()
            return [FileReadError(file)]

        self.identifiers[file] = {}
        import_errors = self._load_imported_files(file, parsed_file, tokens)

        if import_errors:
            self.file_load_stack.pop()
            return import_errors

        try:
            self._load_file_identifiers(file, parsed_file, tokens)
        except TypeException as e:
            self.file_load_stack.pop()
            return [e]

        load_file_exceptions = self._type_check_file(file, parsed_file, tokens)
        if load_file_exceptions:
            self.file_load_stack.pop()
            return load_file_exceptions

        self.function_instructions[file] = self._generate_file_instructions(
            file, parsed_file
        )
        self.file_load_stack.pop()
        return []

    def _parse_regular_file(self, file: Path) -> Tuple[List[Token], ParsedFile]:
        code = file.read_text()
        tokens, tree = parse_aaa(str(file), code, verbose=PARSE_VERBOSE)
        parsed_file = ParsedFile.from_tree(tree, tokens, code)
        return tokens, parsed_file

    def _parse_builtins_file(
        self, file: Path
    ) -> Tuple[List[Token], ParsedBuiltinsFile]:
        code = file.read_text()
        tokens, tree = parse_aaa(str(file), code, verbose=PARSE_VERBOSE)
        parsed_builtins_file = ParsedBuiltinsFile.from_tree(tree, tokens, code)
        return tokens, parsed_builtins_file

    def _load_file_identifiers(
        self, file: Path, parsed_file: ParsedFile, tokens: List[Token]
    ) -> None:
        for function in parsed_file.functions:
            if function.name in self.identifiers[file]:
                raise FunctionNameCollision(file=file, tokens=tokens, function=function)

            self.identifiers[file][function.name] = function

    def _generate_file_instructions(
        self, file: Path, parsed_file: ParsedFile
    ) -> Dict[str, List[Instruction]]:
        file_instructions: Dict[str, List[Instruction]] = {}
        for function in parsed_file.functions:
            file_instructions[function.name] = InstructionGenerator(
                file, function, self
            ).generate_instructions()
        return file_instructions

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

    def _load_imported_files(
        self,
        file: Path,
        parsed_file: ParsedFile,
        tokens: List[Token],
    ) -> List[FileLoadException]:
        errors: List[FileLoadException] = []

        for import_ in parsed_file.imports:
            if import_.source.startswith("/"):
                errors.append(
                    AbsoluteImportError(file=file, tokens=tokens, node=import_)
                )
                continue

            import_path = (file.parent / f"{import_.source}.aaa").resolve()

            import_errors = self._load_file(import_path)
            if import_errors:
                errors += import_errors
                continue

            loaded_identifiers = self.identifiers[import_path]

            for imported_item in import_.imported_items:
                if imported_item.origninal_name not in loaded_identifiers:
                    # TODO change grammar so we can more precisely point to the item that was not found
                    errors.append(
                        ImportedItemNotFound(
                            file=file,
                            tokens=tokens,
                            node=import_,
                            imported_item=imported_item.origninal_name,
                        )
                    )
                    continue

                self.identifiers[file][imported_item.imported_name] = ProgramImport(
                    original_name=imported_item.origninal_name, source_file=import_path
                )

        return errors

    def get_function(self, file: Path, name: str) -> Optional[Function]:
        try:
            identified = self.identifiers[file][name]
        except KeyError:
            # TODO just raise KeyError here?
            return None

        if isinstance(identified, Function):
            return identified
        elif isinstance(identified, ProgramImport):
            return self.get_function(identified.source_file, identified.original_name)
        else:  # pragma: nocover
            assert False

    def get_function_source_and_name(
        self, called_from: Path, called_name: str
    ) -> Tuple[Path, str]:
        identified = self.identifiers[called_from][called_name]

        if isinstance(identified, Function):
            return called_from, called_name
        elif isinstance(identified, ProgramImport):
            return identified.source_file, identified.original_name
        else:  # pragma nocover
            assert False

    def get_instructions(self, file: Path, name: str) -> List[Instruction]:
        return self.function_instructions[file][name]

    def print_all_instructions(self) -> None:  # pragma: nocover
        for functions in self.function_instructions.values():
            for name, instructions in functions.items():

                func_name = format_str(name, max_length=15)

                for ip, instr in enumerate(instructions):
                    instruction = format_str(instr.__repr__(), max_length=30)

                    print(
                        f"DEBUG | {func_name:>15} | IP: {ip:>3} | {instruction:>30}",
                        file=sys.stderr,
                    )

                print(file=sys.stderr)

        print("---", file=sys.stderr)

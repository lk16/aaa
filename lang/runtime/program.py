import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional, Tuple, Union

from lark.exceptions import UnexpectedInput

from lang.exceptions import AaaLoadException
from lang.exceptions.import_ import (
    AbsoluteImportError,
    CyclicImportError,
    FileReadError,
    ImportedItemNotFound,
)
from lang.exceptions.misc import (
    AaaParseException,
    MainFunctionNotFound,
    MissingEnvironmentVariable,
)
from lang.exceptions.naming import CollidingIdentifier
from lang.instruction_generator import InstructionGenerator
from lang.models import AaaModel
from lang.models.instructions import Instruction
from lang.models.parse import (
    BuiltinFunction,
    Function,
    MemberFunctionName,
    ParsedBuiltinsFile,
    ParsedFile,
    Struct,
)
from lang.models.program import ProgramImport
from lang.models.typing import Signature
from lang.parse.parser import aaa_builtins_parser, aaa_source_parser
from lang.parse.transformer import AaaTransformer
from lang.runtime.debug import format_str
from lang.type_checker import TypeChecker

# Identifiable are things identified uniquely by a filepath and name
Identifiable = Function | ProgramImport | Struct | BuiltinFunction


# TODO move this out
class Builtins(AaaModel):
    functions: Dict[str, List[Tuple[BuiltinFunction, Signature]]]

    @classmethod
    def empty(cls) -> "Builtins":
        return Builtins(functions={})


class Program:
    def __init__(self, file: Path) -> None:
        self.entry_point_file = file.resolve()
        self.identifiers: Dict[Path, Dict[str, Identifiable]] = {}
        self.function_instructions: Dict[Path, Dict[str, List[Instruction]]] = {}

        # Used to detect cyclic import loops
        self.file_load_stack: List[Path] = []

        self._builtins, self.file_load_errors = self._load_builtins()

        if self.file_load_errors:
            return

        self.file_load_errors = self._load_file(self.entry_point_file)

    @classmethod
    def without_file(cls, code: str) -> "Program":
        with NamedTemporaryFile(delete=False) as file:
            saved_file = Path(file.name)
            saved_file.write_text(code)
            return cls(file=saved_file)

    def _load_builtins(self) -> Tuple[Builtins, List[AaaLoadException]]:
        builtins = Builtins.empty()

        try:
            stdlib_path = Path(os.environ["AAA_STDLIB_PATH"])
        except KeyError:
            return builtins, [MissingEnvironmentVariable("AAA_STDLIB_PATH")]

        builtins_file = stdlib_path / "builtins.aaa"

        try:
            parsed_file = self._parse_builtins_file(builtins_file)
        except OSError:
            return builtins, [FileReadError(builtins_file)]

        for function in parsed_file.functions:
            if function.name not in builtins.functions:
                builtins.functions[function.name] = []

            signature = Signature.from_builtin_function(function)
            builtins.functions[function.name].append((function, signature))

        return builtins, []

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

    def _load_file(self, file: Path) -> List[AaaLoadException]:
        # TODO make sure the file wasn't loaded already

        if file in self.file_load_stack:
            return [
                CyclicImportError(dependencies=self.file_load_stack, failed_import=file)
            ]

        self.file_load_stack.append(file)

        try:
            parsed_file = self._parse_regular_file(file)
        except OSError:
            self.file_load_stack.pop()
            return [FileReadError(file)]
        except AaaLoadException as e:
            self.file_load_stack.pop()
            return [e]

        self.identifiers[file] = {}
        import_errors = self._load_imported_files(file, parsed_file)

        if import_errors:
            self.file_load_stack.pop()
            return import_errors

        try:
            self._load_file_identifiers(file, parsed_file)
        except AaaLoadException as e:
            self.file_load_stack.pop()
            return [e]

        load_file_exceptions = self._type_check_file(file, parsed_file)
        if load_file_exceptions:
            self.file_load_stack.pop()
            return load_file_exceptions

        self.function_instructions[file] = self._generate_file_instructions(
            file, parsed_file
        )
        self.file_load_stack.pop()
        return []

    def _parse_regular_file(self, file: Path) -> ParsedFile:
        code = file.read_text()

        try:
            tree = aaa_source_parser.parse(code)
        except UnexpectedInput as e:
            raise AaaParseException(file=file, parse_error=e)

        return AaaTransformer().transform(tree)  # type: ignore

    def _parse_builtins_file(self, file: Path) -> ParsedBuiltinsFile:
        code = file.read_text()

        try:
            tree = aaa_builtins_parser.parse(code)
        except UnexpectedInput as e:
            raise AaaParseException(file=file, parse_error=e)

        return AaaTransformer().transform(tree)  # type: ignore

    def _load_file_identifiers(self, file: Path, parsed_file: ParsedFile) -> None:
        identifiables: List[Union[Function, Struct]] = []
        identifiables += parsed_file.functions
        identifiables += parsed_file.structs

        file_identifiers = self.identifiers[file]

        for identifiable in identifiables:
            identifier = identifiable.identify()

            if identifier in file_identifiers:
                found = file_identifiers[identifier]
                raise CollidingIdentifier(
                    file=file, found=found, colliding=identifiable
                )

            file_identifiers[identifier] = identifiable

    def _generate_file_instructions(
        self, file: Path, parsed_file: ParsedFile
    ) -> Dict[str, List[Instruction]]:
        file_instructions: Dict[str, List[Instruction]] = {}
        for function in parsed_file.functions:
            file_instructions[str(function.name)] = InstructionGenerator(
                file, function, self
            ).generate_instructions()
        return file_instructions

    def _type_check_file(
        self, file: Path, parsed_file: ParsedFile
    ) -> List[AaaLoadException]:
        exceptions: List[AaaLoadException] = []

        if file == self.entry_point_file:
            main_found = False
            for function in parsed_file.functions:
                if function.name == "main":
                    main_found = True
                    break

            if not main_found:
                exceptions.append(MainFunctionNotFound(file))

        for function in parsed_file.functions:
            try:
                TypeChecker(file, function, self).check()
            except AaaLoadException as e:
                exceptions.append(e)

        return exceptions

    def _load_imported_files(
        self,
        file: Path,
        parsed_file: ParsedFile,
    ) -> List[AaaLoadException]:
        errors: List[AaaLoadException] = []

        for import_ in parsed_file.imports:
            if import_.source.startswith("/"):
                errors.append(AbsoluteImportError(file=file, import_=import_))
                continue

            import_path = (file.parent / f"{import_.source}.aaa").resolve()

            import_errors = self._load_file(import_path)
            if import_errors:
                errors += import_errors
                continue

            loaded_identifiers = self.identifiers[import_path]

            for imported_item in import_.imported_items:
                if imported_item.origninal_name not in loaded_identifiers:
                    errors.append(
                        ImportedItemNotFound(
                            file=file,
                            import_=import_,
                            imported_item=imported_item.origninal_name,
                        )
                    )
                    continue

                program_import = ProgramImport(
                    imported_name=imported_item.imported_name,
                    original_name=imported_item.origninal_name,
                    source_file=import_path,
                    token=import_.token,
                )

                found = self.get_identifier(file, imported_item.imported_name)

                if found:
                    errors += [
                        CollidingIdentifier(
                            file=file,
                            found=found,
                            colliding=program_import,
                        )
                    ]
                else:
                    self.identifiers[file][imported_item.imported_name] = program_import

        return errors

    def get_identifier(self, file: Path, name: str) -> Optional[Identifiable]:
        # TODO refactor getting builtin identifiers
        if name in self._builtins.functions:
            tuples = self._builtins.functions[name]

            # TODO make signatures unique
            assert len(tuples) == 1

            builtin_func, _ = tuples[0]
            return builtin_func

        try:
            identified = self.identifiers[file][name]
        except KeyError:
            # TODO just raise KeyError here?
            return None

        if isinstance(identified, Function):
            return identified
        elif isinstance(identified, ProgramImport):
            return self.get_identifier(identified.source_file, identified.original_name)
        elif isinstance(identified, Struct):
            return identified
        else:  # pragma: nocover
            assert False

    def get_function_source_and_name(
        self, called_from: Path, called_name: str
    ) -> Tuple[Path, str]:
        identified = self.identifiers[called_from][called_name]

        if isinstance(identified, (Function, Struct)):
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

                if isinstance(name, MemberFunctionName):
                    name = f"{name.type_name}:{name.func_name}"

                func_name = format_str(name, max_length=15)

                for ip, instr in enumerate(instructions):
                    instruction = format_str(instr.__repr__(), max_length=30)

                    print(
                        f"DEBUG | {func_name:>15} | IP: {ip:>3} | {instruction:>30}",
                        file=sys.stderr,
                    )

                print(file=sys.stderr)

        print("---", file=sys.stderr)

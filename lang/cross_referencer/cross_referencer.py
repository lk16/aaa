from pathlib import Path
from typing import Dict, List

from lang.cross_referencer.models import Function, Import, Struct, Unresolved
from lang.parser import models as parser

Identifiable = Function | Import | Struct


class CrossReferencer:
    def __init__(self, parser_output: parser.ParserOutput) -> None:
        self.parsed_files = parser_output.parsed
        self.builtins_path = parser_output.builtins_path
        self.identifiers: Dict[Path, Dict[str, Identifiable]] = {}

    def run(self) -> None:
        for file, parsed_file in self.parsed_files.items():
            self.identifiers[file] = self._load_identifiers(file, parsed_file)

        # TODO Resolve field types of structs

        # TODO Resolve argument/return types of functions

        # TODO resolve identifiers in functions

        # TODO handle exceptions
        ...

    def _load_identifiers(
        self, file: Path, parsed_file: parser.ParsedFile
    ) -> Dict[str, Identifiable]:
        # TODO add type-syntax to builtins and add builtin types
        identifiables_list: List[Identifiable] = []
        identifiables_list += self._load_structs(parsed_file.structs)
        identifiables_list += self._load_functions(parsed_file.functions)
        identifiables_list += self._load_imports(parsed_file.imports)

        identifiers: Dict[str, Identifiable] = {}
        for identifiable in identifiables_list:
            identifier = identifiable.identify()

            if identifier in identifiers:
                # TODO naming collision within same file
                raise NotImplementedError

            identifiers[identifier] = identifiable

        return identifiers

    def _load_structs(self, parsed_structs: List[parser.Struct]) -> List[Struct]:
        # TODO detect field name conflict within struct

        return [
            Struct(
                parsed=parsed_struct,
                fields={name: Unresolved() for (name, _) in parsed_struct.fields},
                name=parsed_struct.name,
            )
            for parsed_struct in parsed_structs
        ]

    def _load_functions(
        self, parsed_functions: List[parser.Function]
    ) -> List[Function]:
        functions: List[Function] = []

        for parsed_function in parsed_functions:
            arguments: Dict[str, Unresolved] = {}

            for parsed_argument in parsed_function.arguments:

                if parsed_argument.name in arguments:
                    # TODO naming conflict
                    raise NotImplementedError

                arguments[parsed_argument.name] = Unresolved()

            function = Function(
                parsed=parsed_function,
                name=parsed_function.get_name(),
                type_name=parsed_function.get_type_name(),
                arguments=arguments,
                body=Unresolved(),
            )

            functions.append(function)

        return functions

    def _load_imports(self, parsed_imports: List[parser.Import]) -> List[Import]:
        imports: List[Import] = []

        for parsed_import in parsed_imports:
            for imported_item in parsed_import.imported_items:

                import_ = Import(
                    parsed=imported_item,
                    source_file=...,  # TODO compute from file containing import
                    source_name=imported_item.origninal_name,
                    imported_name=imported_item.imported_name,
                    source=Unresolved(),
                )

                imports.append(import_)

        return imports

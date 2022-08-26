from pathlib import Path
from typing import Dict, List

from lang.cross_referencer.models import Function, Import, Struct, Type, Unresolved
from lang.parser import models as parser

Identifiable = Function | Import | Struct | Type


class CrossReferencer:
    def __init__(self, parser_output: parser.ParserOutput) -> None:
        self.parsed_files = parser_output.parsed
        self.builtins_path = parser_output.builtins_path
        self.identifiers: Dict[Path, Dict[str, Identifiable]] = {}

    def run(self) -> None:
        for file, parsed_file in self.parsed_files.items():
            self.identifiers[file] = self._load_identifiers(file, parsed_file)

        # TODO remove: print values for debugging
        for file in sorted(self.identifiers.keys()):
            for name in sorted(self.identifiers[file].keys()):
                identified = self.identifiers[file][name]
                print(f"{file} {name} -> {type(identified).__name__}")

        for file, file_identifiers in self.identifiers.items():
            for identifiable in file_identifiers.values():
                if isinstance(identifiable, Import):
                    self._resolve_import(identifiable)
                elif isinstance(identifiable, Struct):
                    self._resolve_struct_fields(file, identifiable)
                elif isinstance(identifiable, Function):
                    self._resolve_function_arguments(identifiable)
                    self._resolve_function_body(identifiable)

        # TODO handle exceptions
        ...

    def _load_identifiers(
        self, file: Path, parsed_file: parser.ParsedFile
    ) -> Dict[str, Identifiable]:
        identifiables_list: List[Identifiable] = []
        identifiables_list += self._load_types(parsed_file.types)
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
                fields={name: Unresolved() for name in parsed_struct.fields.keys()},
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

    def _load_types(self, types: List[parser.TypeLiteral]) -> List[Type]:
        return [
            Type(name=type.name, param_count=len(type.params), parsed=type)
            for type in types
        ]

    def _resolve_import(self, import_: Import) -> None:

        try:
            source_file_identifiers = self.identifiers[import_.source_file]
        except KeyError:
            # TODO file was not parsed ?!?
            raise NotImplementedError

        try:
            source = source_file_identifiers[import_.source_name]
        except KeyError:
            # TODO importing non-existing value (bad), or file was not parsed (verrry bad)
            raise NotImplementedError

        if isinstance(source, Type):
            # TODO There is no syntax that makes this possible currently
            raise NotImplementedError

        if isinstance(source, Import):
            # TODO Indirect importing is forbidden
            raise NotImplementedError

        import_.source = source

    def _get_identifier(self, file: Path, name: str) -> Identifiable:

        try:
            self.identifiers[self.builtins_path][name]
        except KeyError:
            pass

        identifier = self.identifiers[file][name]

        if isinstance(identifier, Import):
            assert not isinstance(identifier.source, Unresolved)
            return identifier.source

        return identifier

    def _resolve_struct_fields(self, file: Path, struct: Struct) -> None:
        for field_name in struct.fields:
            type_name = struct.parsed.fields[field_name].name

            identifier = self._get_identifier(file, type_name)

            if not isinstance(identifier, (Struct, Type)):
                # TODO unexpected identifier kind (import, function, ...)
                raise NotImplementedError

            struct.fields[field_name] = identifier

    def _resolve_function_arguments(self, function: Function) -> None:
        # TODO
        raise NotImplementedError

    def _resolve_function_body(self, function: Function) -> None:
        # TODO
        raise NotImplementedError

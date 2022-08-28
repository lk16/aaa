from pathlib import Path
from typing import Dict, List

from lang.cross_referencer.models import (
    BooleanLiteral,
    Branch,
    CrossReferencerOutput,
    Function,
    FunctionBody,
    FunctionBodyItem,
    Identifiable,
    Identifier,
    IdentifierCallingFunction,
    IdentifierUsingArgument,
    Import,
    IntegerLiteral,
    Loop,
    MemberFunctionName,
    Operator,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
    TypePlaceholder,
    Unresolved,
    VariableType,
)
from lang.parser import models as parser


class CrossReferencer:
    def __init__(self, parser_output: parser.ParserOutput) -> None:
        self.parsed_files = parser_output.parsed
        self.builtins_path = parser_output.builtins_path
        self.identifiers: Dict[Path, Dict[str, Identifiable]] = {}

    def run(self) -> CrossReferencerOutput:
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
                    self._resolve_function_arguments(file, identifiable)
                    identifiable.body = self._resolve_function_body_identifiers(
                        file, identifiable, identifiable.parsed.body
                    )

        # TODO handle exceptions
        ...

        return CrossReferencerOutput(identifiers=self.identifiers)

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
            function = Function(
                parsed=parsed_function,
                name=parsed_function.name,
                struct_name=parsed_function.struct_name,
                arguments={
                    arg_name: Unresolved()
                    for arg_name in parsed_function.arguments.keys()
                },
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

        if not isinstance(source, (Function, Struct)):
            # TODO other things cannot be imported
            # In particular: imports can't be imported as indirect importing is forbidden
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

    def _get_or_create_function_type_placeholder(
        self, file: Path, function: Function, parsed: parser.TypePlaceholder
    ) -> TypePlaceholder:
        type_placeholder = TypePlaceholder(
            parsed=parsed, function=function, name=parsed.name
        )

        file_identifiers = self.identifiers[file]

        identifier = type_placeholder.identify()

        if identifier not in file_identifiers:
            file_identifiers[identifier] = type_placeholder

        found = file_identifiers[identifier]
        assert isinstance(found, TypePlaceholder)
        return found

    def _get_type_identifier(self, file: Path, name: str) -> Type:
        type = self._get_identifier(file, name)

        if not isinstance(type, Type):
            # TODO handle
            raise NotImplementedError

        return type

    def _resolve_function_arguments(self, file: Path, function: Function) -> None:
        for arg_name, parsed_arg in function.parsed.arguments.items():
            parsed_type = parsed_arg.type
            type: Type | TypePlaceholder

            if isinstance(parsed_type, parser.TypePlaceholder):
                is_placeholder = True
                type = self._get_or_create_function_type_placeholder(
                    file, function, parsed_type
                )
                params: List[VariableType] = []

            elif isinstance(parsed_type, parser.TypeLiteral):
                is_placeholder = False
                type = self._get_type_identifier(file, parsed_type.name)  # TODO

                # TODO handle type params
                assert len(parsed_type.params) == 0
                params = []

            else:  # pragma: nocover
                assert False

            function.arguments[arg_name] = VariableType(
                parsed=parsed_type,
                type=type,
                name=arg_name,
                params=params,
                is_placeholder=is_placeholder,
            )

    def _resolve_function_body_identifiers(
        self, file: Path, function: Function, parsed: parser.FunctionBody
    ) -> FunctionBody:
        items: List[FunctionBodyItem] = []

        for parsed_item in parsed.items:
            item: FunctionBodyItem

            if isinstance(parsed_item, parser.Identifier):
                if parsed_item.name in function.arguments:
                    arg_type = function.arguments[parsed_item.name]
                    item = Identifier(
                        **parsed.dict(), kind=IdentifierUsingArgument(arg_type=arg_type)
                    )
                else:
                    try:
                        identifiable = self._get_identifier(file, parsed_item.name)
                    except KeyError:
                        # TODO calling non-existing function
                        raise NotImplementedError

                    if isinstance(identifiable, Function):
                        item = Identifier(
                            **parsed.dict(),
                            kind=IdentifierCallingFunction(function=identifiable),
                        )
                    elif isinstance(identifiable, Struct):
                        # TODO put struct literal on stack
                        raise NotImplementedError
                    else:  # pragma: nocover
                        raise NotImplementedError

            elif isinstance(parsed_item, parser.IntegerLiteral):
                item = IntegerLiteral(**parsed_item.dict())
            elif isinstance(parsed_item, parser.StringLiteral):
                item = StringLiteral(**parsed_item.dict())
            elif isinstance(parsed_item, parser.BooleanLiteral):
                item = BooleanLiteral(**parsed_item.dict())
            elif isinstance(parsed_item, parser.Operator):
                item = Operator(**parsed_item.dict())
            elif isinstance(parsed_item, parser.Loop):
                item = Loop(
                    condition=self._resolve_function_body_identifiers(
                        file, function, parsed_item.condition
                    ),
                    body=self._resolve_function_body_identifiers(
                        file, function, parsed_item.body
                    ),
                )
            elif isinstance(parsed_item, parser.Branch):
                item = Branch(
                    condition=self._resolve_function_body_identifiers(
                        file, function, parsed_item.condition
                    ),
                    if_body=self._resolve_function_body_identifiers(
                        file, function, parsed_item.if_body
                    ),
                    else_body=self._resolve_function_body_identifiers(
                        file, function, parsed_item.else_body
                    ),
                )
            elif isinstance(parsed_item, parser.MemberFunctionName):
                item = MemberFunctionName(**parsed_item.dict())
            elif isinstance(parsed_item, parser.StructFieldQuery):
                item = StructFieldQuery(**parsed_item.dict())
            elif isinstance(parsed_item, parser.StructFieldUpdate):
                item = StructFieldUpdate(**parsed_item.dict())
            elif isinstance(parsed_item, parser.FunctionBody):
                item = self._resolve_function_body_identifiers(
                    file, function, parsed_item
                )
            else:  # pragma: nocover
                assert False

            items.append(item)

        return FunctionBody(items=items)

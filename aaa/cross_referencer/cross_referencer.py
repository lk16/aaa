import typing
from pathlib import Path
from typing import List, Tuple, TypeVar

from lark.lexer import Token

from aaa.cross_referencer.exceptions import (
    CollidingIdentifier,
    CrossReferenceBaseException,
    ImportedItemNotFound,
    IndirectImportException,
    InvalidType,
    InvalidTypeParameter,
    UnknownIdentifier,
)
from aaa.cross_referencer.models import (
    BooleanLiteral,
    Branch,
    CrossReferencerOutput,
    Function,
    FunctionBody,
    FunctionBodyItem,
    Identifiable,
    IdentifiablesDict,
    Identifier,
    IdentifierCallingFunction,
    IdentifierCallingType,
    IdentifierUsingArgument,
    Import,
    IntegerLiteral,
    Loop,
    MemberFunctionName,
    Operator,
    StringLiteral,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
    Unresolved,
    VariableType,
)
from aaa.parser import models as parser


class CrossReferencer:
    def __init__(self, parser_output: parser.ParserOutput) -> None:
        self.parsed_files = parser_output.parsed
        self.builtins_path = parser_output.builtins_path
        self.identifiers: IdentifiablesDict = {}
        self.exceptions: List[CrossReferenceBaseException] = []

    def run(self) -> CrossReferencerOutput:
        identifiers_list = self._load_identifiers()
        self.identifiers, colissions = self._detect_duplicate_identifiers(
            identifiers_list
        )
        self.exceptions += colissions

        for file, identifier, import_ in self._get_identifiers_by_type(Import):
            try:
                self._resolve_import(file, import_)
            except CrossReferenceBaseException as e:
                self.exceptions.append(e)
                del self.identifiers[(file, identifier)]

        for file, identifier, type in self._get_identifiers_by_type(Type):
            try:
                self._resolve_type_fields(file, type)
            except CrossReferenceBaseException as e:
                self.exceptions.append(e)
                del self.identifiers[(file, identifier)]

        for file, identifier, function in self._get_identifiers_by_type(Function):
            try:
                self._resolve_function_type_params(file, function)
                self._resolve_function_arguments(file, function)
                function.body = self._resolve_function_body_identifiers(
                    file, function, function.parsed.body
                )
            except CrossReferenceBaseException as e:
                self.exceptions.append(e)
                del self.identifiers[(file, identifier)]

        return CrossReferencerOutput(
            identifiers=self.identifiers, exceptions=self.exceptions
        )

    def _load_identifiers(self) -> List[Tuple[Path, Identifiable]]:
        identifiables_list: List[Tuple[Path, Identifiable]] = []
        for file, parsed_file in self.parsed_files.items():
            identifiables_list += self._load_types(file, parsed_file.types)
            identifiables_list += self._load_struct_types(file, parsed_file.structs)
            identifiables_list += self._load_functions(file, parsed_file.functions)
            identifiables_list += self._load_imports(file, parsed_file.imports)
        return identifiables_list

    def _detect_duplicate_identifiers(
        self, identifiables_list: List[Tuple[Path, Identifiable]]
    ) -> Tuple[IdentifiablesDict, List[CollidingIdentifier]]:
        identifiers: IdentifiablesDict = {}
        collisions: List[CollidingIdentifier] = []

        for file, identifiable in identifiables_list:
            key = (file, identifiable.identify())

            if key in identifiers:
                collisions.append(
                    CollidingIdentifier(
                        file=file, colliding=identifiable, found=identifiers[key]
                    )
                )
                continue

            identifiers[key] = identifiable

        return identifiers, collisions

    def _load_struct_types(
        self, file: Path, parsed_structs: List[parser.Struct]
    ) -> List[Tuple[Path, Type]]:
        types: List[Tuple[Path, Type]] = []

        for parsed_struct in parsed_structs:
            type = Type(
                parsed=parsed_struct,
                fields={name: Unresolved() for name in parsed_struct.fields.keys()},
                name=parsed_struct.identifier.name,
                param_count=0,
            )

            types.append((file, type))
        return types

    def _load_functions(
        self, file: Path, parsed_functions: List[parser.Function]
    ) -> List[Tuple[Path, Function]]:
        functions: List[Tuple[Path, Function]] = []

        for parsed_function in parsed_functions:
            struct_name, func_name = parsed_function.get_names()

            function = Function(
                parsed=parsed_function,
                struct_name=struct_name,
                name=func_name,
                arguments=Unresolved(),
                type_params=Unresolved(),
                return_types=Unresolved(),
                body=Unresolved(),
            )

            functions.append((file, function))

        return functions

    def _load_imports(
        self, file: Path, parsed_imports: List[parser.Import]
    ) -> List[Tuple[Path, Import]]:
        imports: List[Tuple[Path, Import]] = []

        for parsed_import in parsed_imports:
            for imported_item in parsed_import.imported_items:

                source_file = file.parent / f"{parsed_import.source}.aaa"

                import_ = Import(
                    parsed=imported_item,
                    source_file=source_file,
                    source_name=imported_item.original_name,
                    imported_name=imported_item.imported_name,
                    source=Unresolved(),
                )

                imports.append((file, import_))

        return imports

    def _load_types(
        self, file: Path, types: List[parser.TypeLiteral]
    ) -> List[Tuple[Path, Type]]:
        return [
            (
                file,
                Type(
                    name=type.identifier.name,
                    param_count=len(type.params.value),
                    parsed=type,
                    fields={},
                ),
            )
            for type in types
        ]

    def _resolve_import(self, file: Path, import_: Import) -> None:

        key = (import_.source_file, import_.source_name)

        try:
            source = self.identifiers[key]
        except KeyError:
            raise ImportedItemNotFound(file=file, import_=import_)

        if isinstance(source, Import):
            raise IndirectImportException(file=file, import_=import_)

        import_.source = source

    def _get_identifier(self, file: Path, name: str, token: Token) -> Identifiable:
        builtins_key = (self.builtins_path, name)
        key = (file, name)

        if builtins_key in self.identifiers:
            found = self.identifiers[builtins_key]
        elif key in self.identifiers:
            found = self.identifiers[key]
        else:
            raise UnknownIdentifier(file=file, name=name, token=token)

        if isinstance(found, Import):
            assert not isinstance(found.source, (Unresolved, Import))
            return found.source

        return found

    T = TypeVar("T")

    def _get_identifiers_by_type(
        self, type: typing.Type[T]
    ) -> List[Tuple[Path, str, T]]:
        return [
            (file, identifier, identifiable)
            for (file, identifier), identifiable in self.identifiers.items()
            if isinstance(identifiable, type)
        ]

    def _resolve_type_fields(self, file: Path, type: Type) -> None:
        for field_name in type.fields:
            if isinstance(type.parsed, parser.Struct):
                type_identifier = type.parsed.fields[field_name].identifier
                type_name = type_identifier.name
                type_token = type_identifier.token

                type.fields[field_name] = self._get_identifier(
                    file, type_name, type_token
                )

    def _resolve_function_type_params(self, file: Path, function: Function) -> None:
        function.type_params = {}

        for parsed_type_param in function.parsed.type_params:
            param_name = parsed_type_param.identifier.name

            type_literal = function.parsed.get_type_param(param_name)

            assert type_literal

            type = Type(parsed=type_literal, name=param_name, param_count=0, fields={})

            if (file, param_name) in self.identifiers:
                # Another identifier in the same file has this name.
                raise CollidingIdentifier(
                    file=file,
                    colliding=type,
                    found=self.identifiers[(file, param_name)],
                )

            function.type_params[param_name] = type

    def _resolve_function_arguments(self, file: Path, function: Function) -> None:
        assert not isinstance(function.type_params, Unresolved)
        function.arguments = []

        for parsed_arg in function.parsed.arguments:
            parsed_type = parsed_arg.type
            arg_type_name = parsed_arg.type.identifier.name
            type: Identifiable | Unresolved

            if arg_type_name in function.type_params:
                type = function.type_params[arg_type_name]
            else:
                type = self._get_identifier(
                    file, parsed_type.identifier.name, parsed_type.identifier.token
                )

            if not isinstance(type, Type):
                # type_params should already be resolved
                assert not isinstance(type, Unresolved)

                raise InvalidTypeParameter(file=file, identifiable=type)

            if arg_type_name in function.type_params:
                params: List[VariableType] = []
            else:
                params = self._resolve_function_argument_params(
                    file, function, parsed_type
                )

            function.arguments.append(
                VariableType(
                    parsed=parsed_type,
                    type=type,
                    name=parsed_type.identifier.name,
                    params=params,
                    is_placeholder=arg_type_name in function.type_params,
                )
            )

    def _resolve_function_argument_params(
        self,
        file: Path,
        function: Function,
        parsed_type: parser.TypeLiteral,
    ) -> List[VariableType]:
        assert not isinstance(function.type_params, Unresolved)
        params: List[VariableType] = []

        for param in parsed_type.params.value:
            assert len(param.params.value) == 0

            param_name = param.identifier.name
            if param_name in function.type_params:
                param_type = function.type_params[param_name]
                assert isinstance(param_type, Type)

                params.append(
                    VariableType(
                        type=param_type,
                        name=param_name,
                        is_placeholder=True,
                        parsed=param,
                        params=[],
                    )
                )
            else:
                identifier = self._get_identifier(
                    file,
                    parsed_type.identifier.name,
                    parsed_type.identifier.token,
                )

                if not isinstance(identifier, Type):
                    raise InvalidType(file=file, identifiable=identifier)

                params.append(
                    VariableType(
                        type=identifier,
                        name=param_name,
                        is_placeholder=False,
                        parsed=param,
                        params=[],
                    )
                )

        return params

    def _resolve_function_body_identifiers(
        self, file: Path, function: Function, parsed: parser.FunctionBody
    ) -> FunctionBody:
        assert not isinstance(function.arguments, Unresolved)
        items: List[FunctionBodyItem] = []

        for parsed_item in parsed.items:
            item: FunctionBodyItem

            if isinstance(parsed_item, parser.Identifier):
                if parsed_item.name in function.arguments:
                    arg_type = next(
                        argument
                        for argument in function.arguments
                        if argument.name == parsed_item.name
                    )

                    assert not isinstance(arg_type, Unresolved)

                    item = Identifier(
                        parsed=parsed_item,
                        kind=IdentifierUsingArgument(arg_type=arg_type),
                    )
                else:
                    identifiable = self._get_identifier(
                        file, parsed_item.name, parsed_item.token
                    )

                    if isinstance(identifiable, Function):
                        item = Identifier(
                            parsed=parsed_item,
                            kind=IdentifierCallingFunction(function=identifiable),
                        )
                    elif isinstance(identifiable, Type):
                        item = Identifier(
                            parsed=parsed_item,
                            kind=IdentifierCallingType(type=identifiable),
                        )
                    else:  # pragma: nocover
                        raise NotImplementedError

            elif isinstance(parsed_item, parser.IntegerLiteral):
                item = IntegerLiteral(parsed=parsed_item)
            elif isinstance(parsed_item, parser.StringLiteral):
                item = StringLiteral(parsed=parsed_item)
            elif isinstance(parsed_item, parser.BooleanLiteral):
                item = BooleanLiteral(parsed=parsed_item)
            elif isinstance(parsed_item, parser.Operator):
                item = Operator(parsed=parsed_item)
            elif isinstance(parsed_item, parser.Loop):
                item = Loop(
                    parsed=parsed_item,
                    condition=self._resolve_function_body_identifiers(
                        file, function, parsed_item.condition
                    ),
                    body=self._resolve_function_body_identifiers(
                        file, function, parsed_item.body
                    ),
                )
            elif isinstance(parsed_item, parser.Branch):
                item = Branch(
                    parsed=parsed_item,
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
            elif isinstance(parsed_item, parser.MemberFunctionLiteral):
                item = MemberFunctionName(parsed=parsed_item)
            elif isinstance(parsed_item, parser.StructFieldQuery):
                item = StructFieldQuery(parsed=parsed_item)
            elif isinstance(parsed_item, parser.StructFieldUpdate):
                item = StructFieldUpdate(parsed=parsed_item)
            elif isinstance(parsed_item, parser.FunctionBody):
                item = self._resolve_function_body_identifiers(
                    file, function, parsed_item
                )
            else:  # pragma: nocover
                assert False

            items.append(item)

        return FunctionBody(items=items)

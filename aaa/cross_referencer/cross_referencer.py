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
    Argument,
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
            identifiers=self.identifiers,
            builtins_path=self.builtins_path,
            exceptions=self.exceptions,
        )

    def _load_identifiers(self) -> List[Identifiable]:
        identifiables: List[Identifiable] = []
        for file, parsed_file in self.parsed_files.items():
            identifiables += self._load_types(file, parsed_file.types)
            identifiables += self._load_struct_types(file, parsed_file.structs)
            identifiables += self._load_functions(file, parsed_file.functions)
            identifiables += self._load_imports(file, parsed_file.imports)
        return identifiables

    def _detect_duplicate_identifiers(
        self, identifiables: List[Identifiable]
    ) -> Tuple[IdentifiablesDict, List[CollidingIdentifier]]:
        identifiers: IdentifiablesDict = {}
        collisions: List[CollidingIdentifier] = []

        for identifiable in identifiables:
            key = identifiable.identify()

            if key in identifiers:
                collisions.append(
                    CollidingIdentifier(
                        file=identifiable.file,
                        colliding=identifiable,
                        found=identifiers[key],
                    )
                )
                continue

            identifiers[key] = identifiable

        return identifiers, collisions

    def _load_struct_types(
        self, file: Path, parsed_structs: List[parser.Struct]
    ) -> List[Type]:
        return [
            Type(
                parsed=parsed_struct,
                fields={name: Unresolved() for name in parsed_struct.fields.keys()},
                name=parsed_struct.identifier.name,
                param_count=0,
                file=file,
            )
            for parsed_struct in parsed_structs
        ]

    def _load_functions(
        self, file: Path, parsed_functions: List[parser.Function]
    ) -> List[Function]:
        functions: List[Function] = []

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
                file=file,
            )

            functions.append(function)

        return functions

    def _load_imports(
        self, file: Path, parsed_imports: List[parser.Import]
    ) -> List[Import]:
        imports: List[Import] = []

        for parsed_import in parsed_imports:
            for imported_item in parsed_import.imported_items:

                source_file = file.parent / f"{parsed_import.source}.aaa"

                import_ = Import(
                    parsed=imported_item,
                    source_file=source_file,
                    source_name=imported_item.original_name,
                    imported_name=imported_item.imported_name,
                    source=Unresolved(),
                    file=file,
                )

                imports.append(import_)

        return imports

    def _load_types(self, file: Path, types: List[parser.TypeLiteral]) -> List[Type]:
        return [
            Type(
                name=type.identifier.name,
                param_count=len(type.params.value),
                parsed=type,
                fields={},
                file=file,
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

                field_type = self._get_identifier(file, type_name, type_token)

                if not isinstance(field_type, Type):
                    # TODO field is import/function/...
                    raise NotImplementedError

                # TODO handle params
                assert field_type.param_count == 0

                assert isinstance(field_type.parsed, parser.TypeLiteral)

                field_var_type = VariableType(
                    parsed=field_type.parsed,
                    type=field_type,
                    name=field_type.name,
                    params=[],
                    is_placeholder=False,
                    file=file,
                )

                type.fields[field_name] = field_var_type

    def _resolve_function_type_params(self, file: Path, function: Function) -> None:
        function.type_params = {}

        for parsed_type_param in function.parsed.type_params:
            param_name = parsed_type_param.identifier.name

            type_literal = function.parsed.get_type_param(param_name)

            assert type_literal

            type = Type(
                parsed=type_literal,
                name=param_name,
                param_count=0,
                fields={},
                file=file,
            )

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

            argument = Argument(
                name=parsed_arg.identifier.name,
                file=file,
                type=VariableType(
                    parsed=parsed_type,
                    type=type,
                    name=parsed_type.identifier.name,
                    params=params,
                    is_placeholder=arg_type_name in function.type_params,
                    file=file,
                ),
            )

            function.arguments.append(argument)

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
                        file=file,
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
                        file=file,
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
                argument = function.get_argument(parsed_item.name)

                if argument:
                    arg_type = argument.type
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

        return FunctionBody(items=items, file=file)

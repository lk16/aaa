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
        self.entrypoint = parser_output.entrypoint
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

        for file, identifier, type_ in self._get_identifiers_by_type(Type):
            try:
                self._resolve_type_fields(file, type_)
            except CrossReferenceBaseException as e:
                self.exceptions.append(e)
                del self.identifiers[(file, identifier)]

        for file, identifier, function in self._get_identifiers_by_type(Function):
            try:
                self._resolve_function_type_params(function)
                self._resolve_function_arguments(function)
                self._resolve_function_return_types(function)
                self._resolve_function_body(function)
                self._resolve_function_body_identifiers(function)

            except CrossReferenceBaseException as e:
                self.exceptions.append(e)
                del self.identifiers[(file, identifier)]

        return CrossReferencerOutput(
            functions={
                k: v for (k, v) in self.identifiers.items() if isinstance(v, Function)
            },
            types={k: v for (k, v) in self.identifiers.items() if isinstance(v, Type)},
            imports={
                k: v for (k, v) in self.identifiers.items() if isinstance(v, Import)
            },
            builtins_path=self.builtins_path,
            entrypoint=self.entrypoint,
            exceptions=self.exceptions,
        )

    def print_values(self) -> None:
        # TODO use this function with a commandline switch

        for (file, identifier), identifiable in self.identifiers.items():

            print(f"{type(identifiable).__name__} {file}:{identifier}")

            if isinstance(identifiable, Function):
                assert not isinstance(identifiable.arguments, Unresolved)
                for arg in identifiable.arguments:
                    if arg.type.is_placeholder:
                        print(f"- arg {arg.name} of placeholder type {arg.type.name}")
                    else:
                        print(
                            f"- arg {arg.name} of type {arg.type.file}:{arg.type.name}"
                        )

                assert not isinstance(identifiable.return_types, Unresolved)
                for return_type in identifiable.return_types:
                    if return_type.is_placeholder:
                        print(f"- return placeholder type {return_type.type.name}")
                    else:
                        print(
                            f"- return type {return_type.type.file}:{return_type.type.name}"
                        )

            elif isinstance(identifiable, Type):
                assert not isinstance(identifiable.fields, Unresolved)

                for field_name, field_var_type in identifiable.fields.items():
                    assert not isinstance(field_var_type, Unresolved)
                    print(
                        f"- field {field_name} of type {field_var_type.file}:{field_var_type.name}"
                    )

            else:
                # TODO add debug print for import
                raise NotImplementedError
            print("\n")

    def _load_identifiers(self) -> List[Identifiable]:
        identifiables: List[Identifiable] = []
        for parsed_file in self.parsed_files.values():
            identifiables += self._load_types(parsed_file.types)
            identifiables += self._load_struct_types(parsed_file.structs)
            identifiables += self._load_functions(parsed_file.functions)
            identifiables += self._load_imports(parsed_file.imports)
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

    def _load_struct_types(self, parsed_structs: List[parser.Struct]) -> List[Type]:
        return [
            Type(parsed=parsed_struct, fields=Unresolved(), param_count=0)
            for parsed_struct in parsed_structs
        ]

    def _load_functions(
        self, parsed_functions: List[parser.Function]
    ) -> List[Function]:
        return [
            Function(
                parsed=parsed_function,
                arguments=Unresolved(),
                type_params=Unresolved(),
                return_types=Unresolved(),
                body=Unresolved(),
            )
            for parsed_function in parsed_functions
        ]

    def _load_imports(self, parsed_imports: List[parser.Import]) -> List[Import]:
        imports: List[Import] = []

        for parsed_import in parsed_imports:
            for imported_item in parsed_import.imported_items:

                source_file = imported_item.file.parent / f"{parsed_import.source}.aaa"

                import_ = Import(
                    parsed=imported_item,
                    source_file=source_file,
                    source_name=imported_item.original_name,
                    imported_name=imported_item.imported_name,
                    source=Unresolved(),
                )

                imports.append(import_)

        return imports

    def _load_types(self, types: List[parser.TypeLiteral]) -> List[Type]:
        return [
            Type(
                param_count=len(type.params.value),
                parsed=type,
                fields={},
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
        type.fields = {}

        for field_name, parsed_field in type.parsed_field_types.items():
            type_identifier = parsed_field.identifier
            type_name = type_identifier.name
            type_token = type_identifier.token

            field_type = self._get_identifier(file, type_name, type_token)

            if not isinstance(field_type, Type):
                # TODO field is import/function/...
                raise NotImplementedError

            # TODO handle params
            assert field_type.param_count == 0

            field_var_type = VariableType(
                parsed=parsed_field,
                type=field_type,
                params=[],
                is_placeholder=False,
            )

            type.fields[field_name] = field_var_type

    def _resolve_function_type_params(self, function: Function) -> None:
        function.type_params = {}

        for parsed_type_param in function.parsed_type_params:
            param_name = parsed_type_param.identifier.name

            type_literal = function.get_parsed_type_param(param_name)

            assert type_literal

            type = Type(
                parsed=type_literal,
                param_count=0,
                fields={},
            )

            if (function.file, param_name) in self.identifiers:
                # Another identifier in the same file has this name.
                raise CollidingIdentifier(
                    file=function.file,
                    colliding=type,
                    found=self.identifiers[(function.file, param_name)],
                )

            function.type_params[param_name] = type

    def _resolve_function_arguments(self, function: Function) -> None:
        assert not isinstance(function.type_params, Unresolved)
        function.arguments = []

        for parsed_arg in function.parsed_arguments:
            parsed_type = parsed_arg.type
            arg_type_name = parsed_arg.type.identifier.name
            type: Identifiable | Unresolved

            if arg_type_name in function.type_params:
                type = function.type_params[arg_type_name]
                params: List[VariableType] = []
            else:
                type = self._get_identifier(
                    function.file,
                    parsed_type.identifier.name,
                    parsed_type.identifier.token,
                )

                if not isinstance(type, Type):
                    raise InvalidTypeParameter(file=function.file, identifiable=type)

                params = self._resolve_function_argument_params(
                    function.file, function, parsed_type
                )

            argument = Argument(
                name=parsed_arg.identifier.name,
                file=function.file,
                type=VariableType(
                    parsed=parsed_type,
                    type=type,
                    params=params,
                    is_placeholder=arg_type_name in function.type_params,
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

                params.append(
                    VariableType(
                        type=param_type,
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
                        is_placeholder=False,
                        parsed=param,
                        params=[],
                    )
                )

        return params

    def _resolve_function_return_types(self, function: Function) -> None:
        assert not isinstance(function.type_params, Unresolved)
        function.return_types = []

        for parsed_return_type in function.parsed_return_types:
            return_type_name = parsed_return_type.identifier.name
            type: Identifiable | Unresolved

            if return_type_name in function.type_params:
                type = function.type_params[return_type_name]
                params: List[VariableType] = []
            else:
                type = self._get_identifier(
                    function.file,
                    parsed_return_type.identifier.name,
                    parsed_return_type.identifier.token,
                )

                if not isinstance(type, Type):
                    raise InvalidTypeParameter(file=function.file, identifiable=type)

                params = []
                for parsed_param in parsed_return_type.params.value:
                    param_name = parsed_param.identifier.name

                    if param_name in function.type_params:
                        param_var_type = VariableType(
                            is_placeholder=True,
                            params=[],
                            parsed=parsed_param,
                            type=function.type_params[param_name],
                        )
                    else:
                        identifier = self._get_identifier(
                            function.file,
                            parsed_param.identifier.name,
                            parsed_param.identifier.token,
                        )

                        if not isinstance(identifier, Type):
                            raise InvalidType(
                                file=function.file, identifiable=identifier
                            )

                        param_var_type = VariableType(
                            is_placeholder=False,
                            params=[],
                            parsed=parsed_param,
                            type=identifier,
                        )

                    params.append(param_var_type)

            return_type = VariableType(
                parsed=parsed_return_type,
                type=type,
                params=params,
                is_placeholder=return_type_name in function.type_params,
            )

            function.return_types.append(return_type)

    def _resolve_function_body(self, function: Function) -> None:
        def resolve_body(parsed_body: parser.FunctionBody) -> FunctionBody:
            return FunctionBody(
                items=[resolve_item(item) for item in parsed_body.items],
                parsed=parsed_body,
            )

        def resolve_item(parsed_item: parser.FunctionBodyItem) -> FunctionBodyItem:
            if isinstance(parsed_item, parser.IntegerLiteral):
                return IntegerLiteral(parsed=parsed_item)
            elif isinstance(parsed_item, parser.StringLiteral):
                return StringLiteral(parsed=parsed_item)
            elif isinstance(parsed_item, parser.BooleanLiteral):
                return BooleanLiteral(parsed=parsed_item)
            elif isinstance(parsed_item, parser.Operator):
                return Identifier(
                    parsed=parser.Identifier(
                        file=parsed_item.file,
                        token=parsed_item.token,
                        name=parsed_item.value,
                    ),
                    kind=Unresolved(),
                )
            elif isinstance(parsed_item, parser.Loop):
                return Loop(
                    condition=resolve_body(parsed_item.condition),
                    body=resolve_body(parsed_item.body),
                    parsed=parsed_item,
                )
            elif isinstance(parsed_item, parser.Identifier):
                return Identifier(kind=Unresolved(), parsed=parsed_item)
            elif isinstance(parsed_item, parser.Branch):
                return Branch(
                    condition=resolve_body(parsed_item.condition),
                    if_body=resolve_body(parsed_item.if_body),
                    else_body=resolve_body(parsed_item.else_body),
                    parsed=parsed_item,
                )
            elif isinstance(parsed_item, parser.MemberFunctionLiteral):
                return MemberFunctionName(parsed=parsed_item)
            elif isinstance(parsed_item, parser.StructFieldQuery):
                return StructFieldQuery(parsed=parsed_item)
            elif isinstance(parsed_item, parser.StructFieldUpdate):
                return StructFieldUpdate(
                    parsed=parsed_item,
                    new_value_expr=resolve_body(parsed_item.new_value_expr),
                )
            else:  # pragma: nocover
                assert False

        function.body = resolve_body(function.parsed_body)

    def _resolve_function_body_identifiers(self, function: Function) -> None:
        def resolve_identifier(identifier: Identifier) -> None:
            argument = function.get_argument(identifier.name)

            if argument:
                arg_type = argument.type
                assert not isinstance(arg_type, Unresolved)

                identifier.kind = IdentifierUsingArgument(arg_type=arg_type)
            else:
                identifiable = self._get_identifier(
                    function.file, identifier.name, identifier.token
                )

                if isinstance(identifiable, Function):
                    identifier.kind = IdentifierCallingFunction(function=identifiable)
                elif isinstance(identifiable, Type):
                    identifier.kind = IdentifierCallingType(type=identifiable)
                else:  # pragma: nocover
                    raise NotImplementedError

        def resolve(function_body: FunctionBody) -> None:
            for item in function_body.items:
                if isinstance(item, Loop):
                    resolve(item.condition)
                    resolve(item.body)
                elif isinstance(item, Branch):
                    resolve(item.condition)
                    resolve(item.if_body)
                    resolve(item.else_body)
                elif isinstance(item, StructFieldUpdate):
                    resolve(item.new_value_expr)
                elif isinstance(item, Identifier):
                    resolve_identifier(item)

        assert not isinstance(function.arguments, Unresolved)
        assert not isinstance(function.body, Unresolved)

        resolve(function.body)

import typing
from pathlib import Path
from typing import List, Tuple, TypeVar

from aaa import AaaRunnerException
from aaa.cross_referencer.exceptions import (
    CollidingIdentifier,
    CrossReferenceBaseException,
    ImportedItemNotFound,
    IndirectImportException,
    InvalidType,
    InvalidTypeParameter,
    MainFunctionNotFound,
    MainIsNotAFunction,
    UnexpectedTypeParameterCount,
    UnknownIdentifier,
)
from aaa.cross_referencer.models import (
    Argument,
    ArgumentIdentifiable,
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
    StringLiteral,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
    Unresolved,
    VariableType,
)
from aaa.parser import models as parser
from aaa.parser.transformer import DUMMY_TOKEN


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
                self._resolve_import(import_)
            except CrossReferenceBaseException as e:
                self.exceptions.append(e)
                del self.identifiers[(file, identifier)]

        for file, identifier, type_ in self._get_identifiers_by_type(Type):
            try:
                self._resolve_type_fields(type_)
            except CrossReferenceBaseException as e:
                self.exceptions.append(e)
                del self.identifiers[(file, identifier)]

        try:
            self._resolve_main_function()
        except CrossReferenceBaseException as e:
            self.exceptions.append(e)

        for file, identifier, function in self._get_identifiers_by_type(Function):
            try:
                self._resolve_function_params(function)
                self._check_function_argument_collision(function)
                self._resolve_function_arguments(function)
                self._check_argument_identifier_collision(function)
                self._resolve_function_return_types(function)
                self._resolve_function_body(function)
                self._resolve_function_body_identifiers(function)

            except CrossReferenceBaseException as e:
                self.exceptions.append(e)
                del self.identifiers[(file, identifier)]

        if self.exceptions:
            raise AaaRunnerException(self.exceptions)

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
        )

    def print_values(self) -> None:
        # TODO use this function with a commandline switch

        for (file, identifier), identifiable in self.identifiers.items():

            print(f"{type(identifiable).__name__} {file}:{identifier}")

            if isinstance(identifiable, Function):
                assert not isinstance(identifiable.arguments, Unresolved)
                for arg in identifiable.arguments:
                    if arg.var_type.is_placeholder:
                        print(
                            f"- arg {arg.name} of placeholder type {arg.var_type.name}"
                        )
                    else:
                        print(
                            f"- arg {arg.name} of type {arg.var_type.file}:{arg.var_type.name}"
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
                import_ = Import(
                    parsed=imported_item,
                    source_file=parsed_import.source_file,
                    source_name=imported_item.original_name,
                    imported_name=imported_item.imported_name,
                    source=Unresolved(),
                )

                imports.append(import_)

        return imports

    def _load_types(self, types: List[parser.TypeLiteral]) -> List[Type]:
        return [
            Type(
                param_count=len(type.params),
                parsed=type,
                fields={},
            )
            for type in types
        ]

    def _resolve_import(self, import_: Import) -> None:

        key = (import_.source_file, import_.source_name)

        try:
            source = self.identifiers[key]
        except KeyError:
            raise ImportedItemNotFound(file=import_.file, import_=import_)

        if isinstance(source, Import):
            raise IndirectImportException(file=import_.file, import_=import_)

        import_.source = source

    def _get_identifiable(
        self, identifier: parser.Identifier | Identifier  # TODO this union is ugly
    ) -> Identifiable:
        name = identifier.name
        file = identifier.file
        token = identifier.token

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

    def _resolve_type_field(self, parsed_field: parser.TypeLiteral) -> VariableType:
        type_identifier = parsed_field.identifier
        field_type = self._get_identifiable(type_identifier)

        if not isinstance(field_type, Type):
            # TODO field is import/function/...
            raise NotImplementedError

        params: List[VariableType] = []

        for parsed_param in parsed_field.params:
            param_type = self._get_identifiable(parsed_param.identifier)

            if not isinstance(param_type, Type):
                # TODO param_type is import/function/...
                raise NotImplementedError

            assert len(parsed_param.params) == 0

            params.append(
                VariableType(
                    parsed=parsed_param,
                    type=param_type,
                    params=[],
                    is_placeholder=False,
                )
            )

        return VariableType(
            parsed=parsed_field,
            type=field_type,
            params=params,
            is_placeholder=False,
        )

    def _resolve_type_fields(self, type: Type) -> None:
        type.fields = {
            field_name: self._resolve_type_field(parsed_field)
            for field_name, parsed_field in type.parsed_field_types.items()
        }

    def _resolve_function_param(
        self, function: Function, parsed_type_param: parser.TypeLiteral
    ) -> Type:
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

        return type

    def _resolve_function_params(self, function: Function) -> None:
        function.type_params = {
            parsed_type_param.identifier.name: self._resolve_function_param(
                function, parsed_type_param
            )
            for parsed_type_param in function.parsed_type_params
        }

    def _check_function_argument_collision(self, function: Function) -> None:
        arg_count = len(function.parsed_arguments)

        for i in range(arg_count):
            lhs_arg = function.parsed_arguments[i]
            for j in range(i + 1, arg_count):
                rhs_arg = function.parsed_arguments[j]

                if lhs_arg.identifier.name == rhs_arg.identifier.name:
                    lhs_identifiable = ArgumentIdentifiable(
                        file=lhs_arg.file,
                        token=lhs_arg.token,
                        name=lhs_arg.identifier.name,
                    )
                    rhs_identifiable = ArgumentIdentifiable(
                        file=rhs_arg.file,
                        token=rhs_arg.token,
                        name=rhs_arg.identifier.name,
                    )

                    raise CollidingIdentifier(
                        file=function.file,
                        colliding=lhs_identifiable,
                        found=rhs_identifiable,
                    )

    def _resolve_function_argument(
        self, function: Function, parsed_arg: parser.Argument
    ) -> Argument:
        assert not isinstance(function.type_params, Unresolved)
        parsed_type = parsed_arg.type
        arg_type_name = parsed_arg.type.identifier.name
        type: Identifiable | Unresolved

        if arg_type_name in function.type_params:
            type = function.type_params[arg_type_name]
            params: List[VariableType] = []
        else:
            type = self._get_identifiable(parsed_type.identifier)

            if not isinstance(type, Type):
                raise InvalidTypeParameter(file=function.file, identifiable=type)

            if len(parsed_type.params) != type.param_count:
                raise UnexpectedTypeParameterCount(
                    file=function.file,
                    token=parsed_arg.identifier.token,
                    expected_param_count=type.param_count,
                    found_param_count=len(parsed_type.params),
                )

            params = self._lookup_function_params(function, parsed_type)

        return Argument(
            name=parsed_arg.identifier.name,
            file=function.file,
            var_type=VariableType(
                parsed=parsed_type,
                type=type,
                params=params,
                is_placeholder=arg_type_name in function.type_params,
            ),
        )

    def _resolve_function_arguments(self, function: Function) -> None:
        function.arguments = [
            self._resolve_function_argument(function, parsed_arg)
            for parsed_arg in function.parsed_arguments
        ]

    def _lookup_function_param(
        self, function: Function, param: parser.TypeLiteral
    ) -> VariableType:
        assert not isinstance(function.type_params, Unresolved)
        assert len(param.params) == 0

        param_name = param.identifier.name
        if param_name in function.type_params:
            param_type = function.type_params[param_name]
            is_placeholder = True
        else:
            is_placeholder = False
            identifier = self._get_identifiable(param.identifier)

            if not isinstance(identifier, Type):
                raise InvalidType(file=identifier.file, identifiable=identifier)

            param_type = identifier

        return VariableType(
            type=param_type,
            is_placeholder=is_placeholder,
            parsed=param,
            params=self._lookup_function_params(function, param),
        )

    def _lookup_function_params(
        self,
        function: Function,
        parsed_type: parser.TypeLiteral,
    ) -> List[VariableType]:
        return [
            self._lookup_function_param(function, param) for param in parsed_type.params
        ]

    def _check_argument_identifier_collision(self, function: Function) -> None:
        assert not isinstance(function.arguments, Unresolved)

        for argument in function.arguments:
            key = (function.file, argument.name)

            try:
                found = self.identifiers[key]
            except KeyError:
                pass
            else:
                raise CollidingIdentifier(
                    file=argument.file,
                    colliding=ArgumentIdentifiable(
                        file=argument.file, token=argument.token, name=argument.name
                    ),
                    found=found,
                )

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
                type = self._get_identifiable(parsed_return_type.identifier)

                if not isinstance(type, Type):
                    raise InvalidTypeParameter(file=function.file, identifiable=type)

                params = self._lookup_function_params(function, parsed_return_type)

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

        def resolve_param(type_literal: parser.TypeLiteral) -> Identifier:
            return Identifier(
                kind=Unresolved(),
                type_params=[resolve_param(param) for param in type_literal.params],
                parsed=type_literal.identifier,
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
                    type_params=[],
                    kind=Unresolved(),
                )
            elif isinstance(parsed_item, parser.Loop):
                return Loop(
                    condition=resolve_body(parsed_item.condition),
                    body=resolve_body(parsed_item.body),
                    parsed=parsed_item,
                )
            elif isinstance(parsed_item, parser.Branch):
                return Branch(
                    condition=resolve_body(parsed_item.condition),
                    if_body=resolve_body(parsed_item.if_body),
                    else_body=resolve_body(parsed_item.else_body),
                    parsed=parsed_item,
                )
            elif isinstance(parsed_item, parser.FunctionName):
                if parsed_item.struct_name:
                    name = (
                        f"{parsed_item.struct_name.name}:{parsed_item.func_name.name}"
                    )
                else:
                    name = parsed_item.func_name.name

                return Identifier(
                    kind=Unresolved(),
                    type_params=[
                        resolve_param(param) for param in parsed_item.type_params
                    ],
                    parsed=parser.Identifier(
                        name=name,
                        file=parsed_item.file,
                        token=parsed_item.token,
                    ),
                )
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
        def resolve_param_type(identifier: Identifier) -> VariableType:
            # TODO remove dummy_type_literal
            dummy_type_literal = parser.TypeLiteral(
                identifier=parser.Identifier(
                    name=identifier.name,
                    file=Path("/dev/null"),
                    token=DUMMY_TOKEN,
                ),
                params=[],
                file=Path("/dev/null"),
                token=DUMMY_TOKEN,
            )

            type = self._get_identifiable(identifier)

            if not isinstance(type, Type):
                # TODO
                raise NotImplementedError

            return VariableType(
                parsed=dummy_type_literal,
                type=type,
                is_placeholder=False,  # TODO this may not be true
                params=[
                    resolve_param_type(sub_param)
                    for sub_param in identifier.type_params
                ],
            )

        def resolve_identifier(identifier: Identifier) -> None:
            argument = function.get_argument(identifier.name)

            if argument:
                arg_type = argument.var_type
                assert not isinstance(arg_type, Unresolved)

                identifier.kind = IdentifierUsingArgument(arg_type=arg_type)
            else:
                identifiable = self._get_identifiable(identifier)

                if isinstance(identifiable, Function):
                    identifier.kind = IdentifierCallingFunction(function=identifiable)
                elif isinstance(identifiable, Type):

                    # TODO remove dummy_type_literal
                    dummy_type_literal = parser.TypeLiteral(
                        identifier=parser.Identifier(
                            name=identifier.name,
                            file=Path("/dev/null"),
                            token=DUMMY_TOKEN,
                        ),
                        params=[],
                        file=Path("/dev/null"),
                        token=DUMMY_TOKEN,
                    )

                    var_type = VariableType(
                        type=identifiable,
                        is_placeholder=False,  # TODO this may not be true
                        params=[
                            resolve_param_type(param)
                            for param in identifier.type_params
                        ],
                        parsed=dummy_type_literal,
                    )

                    if len(identifier.type_params) != identifiable.param_count:
                        raise UnexpectedTypeParameterCount(
                            file=function.file,
                            token=identifier.token,
                            expected_param_count=identifiable.param_count,
                            found_param_count=len(identifier.type_params),
                        )

                    identifier.kind = IdentifierCallingType(var_type=var_type)
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
                elif isinstance(item, FunctionBody):
                    resolve(item)

        assert not isinstance(function.arguments, Unresolved)
        assert not isinstance(function.body, Unresolved)

        resolve(function.body)

    def _resolve_main_function(self) -> None:
        # TODO move to type_checker

        try:
            main = self.identifiers[(self.entrypoint, "main")]
        except KeyError as e:
            raise MainFunctionNotFound(self.entrypoint) from e

        if not isinstance(main, Function):
            raise MainIsNotAFunction(self.entrypoint, main)

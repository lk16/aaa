import typing
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TypeVar

from aaa import AaaRunnerException
from aaa.cross_referencer.exceptions import (
    CollidingIdentifier,
    CrossReferenceBaseException,
    ImportedItemNotFound,
    IndirectImportException,
    InvalidArgument,
    InvalidType,
    InvalidTypeParameter,
    MainFunctionNotFound,
    MainIsNotAFunction,
    UnexpectedTypeParameterCount,
    UnknownIdentifier,
)
from aaa.cross_referencer.models import (
    AaaCrossReferenceModel,
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
    IdentifierUsingArgument,
    Import,
    IntegerLiteral,
    Loop,
    StringLiteral,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
    UnresolvedFunction,
    UnresolvedImport,
    UnresolvedType,
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

    def _save_identifier(self, identifiable: Identifiable) -> None:
        key = identifiable.identify()

        try:
            found = self.identifiers[key]
        except KeyError:
            self.identifiers[key] = identifiable
        else:
            self.exceptions += [CollidingIdentifier(identifiable, found)]

    def run(self) -> CrossReferencerOutput:
        self._cross_reference_file(self.entrypoint)

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

    def _cross_reference_file(self, file: Path) -> None:
        # TODO prevent cross referencing twice
        # TODO prevent circular dependencies

        dependencies = self.parsed_files[file].dependencies()

        for dependency in dependencies:
            self._cross_reference_file(dependency)

        imports, types, functions = self._load_identifiers(file)

        for unresolved_import in imports:
            try:
                import_ = self._resolve_import(unresolved_import)
            except CrossReferenceBaseException as e:
                self.exceptions.append(e)
            else:
                self._save_identifier(import_)

        for unresolved_type in types:
            try:
                type = self._resolve_type(unresolved_type)
            except CrossReferenceBaseException as e:
                self.exceptions.append(e)
            else:
                self._save_identifier(type)

        for unresolved_function in functions:
            try:
                function = self._resolve_function_signature(unresolved_function)
            except CrossReferenceBaseException as e:
                self.exceptions.append(e)
            else:
                self._save_identifier(function)

        for unresolved_function in functions:
            func = self.identifiers[
                (unresolved_function.position.file, unresolved_function.name)
            ]
            assert isinstance(func, Function)
            try:
                body = self._resolve_function_body_root(
                    unresolved_function, func.type_params, func.arguments
                )
            except CrossReferenceBaseException as e:
                self.exceptions.append(e)
            else:
                func.body = body

    def _resolve_function_signature(self, unresolved: UnresolvedFunction) -> Function:
        self._check_function_argument_collision(unresolved)

        params = self._resolve_function_params(unresolved)
        arguments = self._resolve_function_arguments(unresolved, params)
        return_types = self._resolve_function_return_types(unresolved, params)
        function = Function(unresolved, params, arguments, return_types)
        self._check_argument_identifier_collision(function)

        return function

    def print_values(self) -> None:
        # TODO use this function with a commandline switch

        for (file, identifier), identifiable in self.identifiers.items():

            print(f"{type(identifiable).__name__} {file}:{identifier}")

            if isinstance(identifiable, Function):
                for arg in identifiable.arguments:
                    if arg.var_type.is_placeholder:
                        print(
                            f"- arg {arg.name} of placeholder type {arg.var_type.name}"
                        )
                    else:
                        print(
                            f"- arg {arg.name} of type {arg.var_type.position.file}:{arg.var_type.name}"
                        )

                for return_type in identifiable.return_types:
                    if return_type.is_placeholder:
                        print(f"- return placeholder type {return_type.type.name}")
                    else:
                        print(
                            f"- return type {return_type.type.position.file}:{return_type.type.name}"
                        )

            elif isinstance(identifiable, Type):
                for field_name, field_var_type in identifiable.fields.items():
                    print(
                        f"- field {field_name} of type {field_var_type.position.file}:{field_var_type.name}"
                    )

            else:
                # TODO add debug print for import
                raise NotImplementedError
            print("\n")

    def _load_identifiers(
        self, file: Path
    ) -> Tuple[List[UnresolvedImport], List[UnresolvedType], List[UnresolvedFunction]]:
        imports: List[UnresolvedImport] = []
        types: List[UnresolvedType] = []
        functions: List[UnresolvedFunction] = []

        parsed_file = self.parsed_files[file]

        types += self._load_types(parsed_file.types)
        types += self._load_struct_types(parsed_file.structs)
        functions += self._load_functions(parsed_file.functions)
        imports += self._load_imports(parsed_file.imports)
        return imports, types, functions

    def _load_struct_types(
        self, parsed_structs: List[parser.Struct]
    ) -> List[UnresolvedType]:
        return [
            UnresolvedType(parsed=parsed_struct, param_count=0)
            for parsed_struct in parsed_structs
        ]

    def _load_functions(
        self, parsed: List[parser.Function]
    ) -> List[UnresolvedFunction]:
        return [UnresolvedFunction(parsed_function) for parsed_function in parsed]

    def _load_imports(
        self, parsed_imports: List[parser.Import]
    ) -> List[UnresolvedImport]:
        imports: List[UnresolvedImport] = []

        for parsed_import in parsed_imports:
            for imported_item in parsed_import.imported_items:
                import_ = UnresolvedImport(
                    import_item=imported_item, import_=parsed_import
                )
                imports.append(import_)

        return imports

    def _load_types(self, types: List[parser.TypeLiteral]) -> List[UnresolvedType]:
        return [
            UnresolvedType(param_count=len(type.params), parsed=type) for type in types
        ]

    def _resolve_import(self, import_: UnresolvedImport) -> Import:

        key = (import_.source_file, import_.source_name)

        try:
            source = self.identifiers[key]
        except KeyError:
            raise ImportedItemNotFound(import_)

        if isinstance(source, Import):
            raise IndirectImportException(import_)

        return Import(import_, source)

    def _get_identifiable(
        self, identifier: parser.Identifier | Identifier  # TODO this union is ugly
    ) -> Identifiable:
        name = identifier.name
        file = identifier.position.file

        builtins_key = (self.builtins_path, name)
        key = (file, name)

        if builtins_key in self.identifiers:
            found = self.identifiers[builtins_key]
        elif key in self.identifiers:
            found = self.identifiers[key]
        else:
            raise UnknownIdentifier(identifier.position, name)

        if isinstance(found, Import):
            assert not isinstance(found.source, Import)
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

    def _resolve_type(self, unresolved: UnresolvedType) -> Type:
        fields = {
            field_name: self._resolve_type_field(parsed_field)
            for field_name, parsed_field in unresolved.parsed_field_types.items()
        }
        return Type(unresolved, fields)

    def _resolve_function_param(
        self, function: UnresolvedFunction, parsed_type_param: parser.TypeLiteral
    ) -> Type:
        param_name = parsed_type_param.identifier.name
        type_literal: Optional[parser.TypeLiteral] = None

        for param in function.parsed.type_params:
            if param.identifier.name == param_name:
                type_literal = param

        assert type_literal

        type = Type(UnresolvedType(parsed=type_literal, param_count=0), fields={})

        if (function.position.file, param_name) in self.identifiers:
            # Another identifier in the same file has this name.
            raise CollidingIdentifier(
                colliding=type,
                found=self.identifiers[(function.position.file, param_name)],
            )

        return type

    def _resolve_function_params(self, function: UnresolvedFunction) -> Dict[str, Type]:
        return {
            parsed_type_param.identifier.name: self._resolve_function_param(
                function, parsed_type_param
            )
            for parsed_type_param in function.parsed.type_params
        }

    def _check_function_argument_collision(self, function: UnresolvedFunction) -> None:
        arg_count = len(function.parsed.arguments)

        for i in range(arg_count):
            lhs_arg = function.parsed.arguments[i]
            for j in range(i + 1, arg_count):
                rhs_arg = function.parsed.arguments[j]

                if lhs_arg.identifier.name == rhs_arg.identifier.name:
                    lhs_identifiable = ArgumentIdentifiable(
                        lhs_arg.position, lhs_arg.identifier.name
                    )
                    rhs_identifiable = ArgumentIdentifiable(
                        rhs_arg.position, rhs_arg.identifier.name
                    )

                    raise CollidingIdentifier(
                        colliding=lhs_identifiable,
                        found=rhs_identifiable,
                    )

    def _resolve_function_argument(
        self,
        function: UnresolvedFunction,
        type_params: Dict[str, Type],
        parsed_arg: parser.Argument,
    ) -> Argument:
        parsed_type = parsed_arg.type
        arg_type_name = parsed_arg.type.identifier.name
        type: Identifiable

        found_type_param: Optional[parser.TypeLiteral] = None
        for type_param in function.parsed.type_params:
            if type_param.identifier.name == arg_type_name:
                found_type_param = type_param

        if found_type_param:
            type = type_params[arg_type_name]
            params: List[VariableType] = []
        else:
            type = self._get_identifiable(parsed_type.identifier)

            if not isinstance(type, Type):
                raise InvalidArgument(used=parsed_arg.type, found=type)

            if len(parsed_type.params) != type.param_count:
                raise UnexpectedTypeParameterCount(
                    position=parsed_arg.identifier.position,
                    expected_param_count=type.param_count,
                    found_param_count=len(parsed_type.params),
                )

            params = self._lookup_function_params(type_params, parsed_type)

        return Argument(
            name=parsed_arg.identifier.name,
            var_type=VariableType(
                parsed=parsed_type,
                type=type,
                params=params,
                is_placeholder=arg_type_name in type_params,
            ),
        )

    def _resolve_function_arguments(
        self, function: UnresolvedFunction, type_params: Dict[str, Type]
    ) -> List[Argument]:
        return [
            self._resolve_function_argument(function, type_params, parsed_arg)
            for parsed_arg in function.parsed.arguments
        ]

    def _lookup_function_param(
        self,
        type_params: Dict[str, Type],
        param: parser.TypeLiteral,
    ) -> VariableType:
        assert len(param.params) == 0

        param_name = param.identifier.name
        if param_name in type_params:
            param_type = type_params[param_name]
            is_placeholder = True
        else:
            is_placeholder = False
            identifier = self._get_identifiable(param.identifier)

            if not isinstance(identifier, Type):
                raise InvalidType(identifier)

            param_type = identifier

        return VariableType(
            type=param_type,
            is_placeholder=is_placeholder,
            parsed=param,
            params=self._lookup_function_params(type_params, param),
        )

    def _lookup_function_params(
        self,
        type_params: Dict[str, Type],
        parsed_type: parser.TypeLiteral,
    ) -> List[VariableType]:
        return [
            self._lookup_function_param(type_params, param)
            for param in parsed_type.params
        ]

    def _check_argument_identifier_collision(self, function: Function) -> None:
        for argument in function.arguments:
            key = (function.position.file, argument.name)

            try:
                found = self.identifiers[key]
            except KeyError:
                pass
            else:
                raise CollidingIdentifier(
                    colliding=ArgumentIdentifiable(argument.position, argument.name),
                    found=found,
                )

    def _resolve_function_return_types(
        self, function: UnresolvedFunction, type_params: Dict[str, Type]
    ) -> List[VariableType]:

        return_types: List[VariableType] = []

        for parsed_return_type in function.parsed.return_types:
            return_type_name = parsed_return_type.identifier.name
            type: Identifiable

            if return_type_name in type_params:
                type = type_params[return_type_name]
                params: List[VariableType] = []
            else:
                type = self._get_identifiable(parsed_return_type.identifier)

                if not isinstance(type, Type):
                    raise InvalidTypeParameter(type)

                params = self._lookup_function_params(type_params, parsed_return_type)

            return_type = VariableType(
                parsed=parsed_return_type,
                type=type,
                params=params,
                is_placeholder=return_type_name in type_params,
            )

            return_types.append(return_type)
        return return_types

    def _resolve_function_body(
        self,
        function: UnresolvedFunction,
        params: Dict[str, Type],
        arguments: List[Argument],
        parsed_body: parser.FunctionBody,
    ) -> FunctionBody:
        return FunctionBody(
            items=[
                self._resolve_function_body_item(function, params, arguments, item)
                for item in parsed_body.items
            ],
            parsed=parsed_body,
        )

    def _resolve_function_type_param(
        self, function: UnresolvedFunction, type_literal: parser.TypeLiteral
    ) -> Identifier:
        raise NotImplementedError  # TODO

    def _resolve_operator(
        self,
        function: UnresolvedFunction,
        params: Dict[str, Type],
        arguments: List[Argument],
        operator: parser.Operator,
    ) -> Identifier:
        # TODO make parser output an Identifier for OPERATOR tokens
        identifier = parser.Identifier(operator.position, operator.value)

        operator_func = self._get_identifiable(identifier)
        assert isinstance(operator_func, Function)

        return Identifier(
            parsed=identifier,
            type_params=[],
            kind=IdentifierCallingFunction(operator_func),
        )

    def _resolve_branch(
        self,
        function: UnresolvedFunction,
        params: Dict[str, Type],
        arguments: List[Argument],
        branch: parser.Branch,
    ) -> Branch:
        resolved_else_body: Optional[FunctionBody] = None

        if branch.else_body:
            resolved_else_body = self._resolve_function_body(
                function, params, arguments, branch.else_body
            )

        return Branch(
            condition=self._resolve_function_body(
                function, params, arguments, branch.condition
            ),
            if_body=self._resolve_function_body(
                function, params, arguments, branch.if_body
            ),
            else_body=resolved_else_body,
            parsed=branch,
        )

    def _resolve_loop(
        self,
        function: UnresolvedFunction,
        params: Dict[str, Type],
        arguments: List[Argument],
        loop: parser.Loop,
    ) -> Loop:
        return Loop(
            condition=self._resolve_function_body(
                function, params, arguments, loop.condition
            ),
            body=self._resolve_function_body(function, params, arguments, loop.body),
            parsed=loop,
        )

    def _resolve_function_name(
        self,
        function: UnresolvedFunction,
        params: Dict[str, Type],
        arguments: List[Argument],
        function_name: parser.FunctionName,
    ) -> Identifier:
        if function_name.struct_name:
            name = f"{function_name.struct_name.name}:{function_name.func_name.name}"
        else:
            name = function_name.func_name.name

        # TODO creating a parser.Identifier here is a hack
        identifier = parser.Identifier(function_name.position, name)

        for argument in arguments:
            if name == argument.name:
                return Identifier(
                    kind=IdentifierUsingArgument(argument.var_type),
                    type_params=[],
                    parsed=identifier,
                )

        identifiable = self._get_identifiable(identifier)

        if isinstance(identifiable, Function):
            return Identifier(
                kind=IdentifierCallingFunction(identifiable),
                type_params=[
                    self._resolve_function_type_param(function, param)
                    for param in function_name.type_params
                ],
                parsed=identifier,
            )

        # TODO handle identifiable is a Type
        raise NotImplementedError

    def _resolve_struct_field_update(
        self,
        function: UnresolvedFunction,
        params: Dict[str, Type],
        arguments: List[Argument],
        update: parser.StructFieldUpdate,
    ) -> StructFieldUpdate:
        return StructFieldUpdate(
            parsed=update,
            new_value_expr=self._resolve_function_body(
                function, params, arguments, update.new_value_expr
            ),
        )

    def _resolve_function_body_item(
        self,
        function: UnresolvedFunction,
        params: Dict[str, Type],
        arguments: List[Argument],
        parsed_item: parser.FunctionBodyItem,
    ) -> FunctionBodyItem:
        if isinstance(parsed_item, parser.IntegerLiteral):
            return IntegerLiteral(parsed_item)
        elif isinstance(parsed_item, parser.StringLiteral):
            return StringLiteral(parsed_item)
        elif isinstance(parsed_item, parser.BooleanLiteral):
            return BooleanLiteral(parsed_item)
        elif isinstance(parsed_item, parser.Operator):
            return self._resolve_operator(function, params, arguments, parsed_item)
        elif isinstance(parsed_item, parser.Loop):
            return self._resolve_loop(function, params, arguments, parsed_item)
        elif isinstance(parsed_item, parser.Branch):
            return self._resolve_branch(function, params, arguments, parsed_item)
        elif isinstance(parsed_item, parser.FunctionName):
            return self._resolve_function_name(function, params, arguments, parsed_item)
        elif isinstance(parsed_item, parser.StructFieldQuery):
            return StructFieldQuery(parsed=parsed_item)
        elif isinstance(parsed_item, parser.StructFieldUpdate):
            return self._resolve_struct_field_update(
                function, params, arguments, parsed_item
            )
        else:  # pragma: nocover
            assert False

    def _resolve_function_body_root(
        self,
        function: UnresolvedFunction,
        params: Dict[str, Type],
        arguments: List[Argument],
    ) -> FunctionBody:
        return self._resolve_function_body(
            function, params, arguments, function.parsed.body
        )

    def _resolve_main_function(self) -> None:
        # TODO move to type_checker

        try:
            main = self.identifiers[(self.entrypoint, "main")]
        except KeyError as e:
            raise MainFunctionNotFound(self.entrypoint) from e

        if not isinstance(main, Function):
            raise MainIsNotAFunction(main)

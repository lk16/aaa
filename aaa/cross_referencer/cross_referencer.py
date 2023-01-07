from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from aaa import AaaRunnerException, Position
from aaa.cross_referencer.exceptions import (
    CircularDependencyError,
    CollidingIdentifier,
    CrossReferenceBaseException,
    ImportedItemNotFound,
    IndirectImportException,
    InvalidArgument,
    InvalidReturnType,
    InvalidType,
    UnexpectedTypeParameterCount,
    UnknownIdentifier,
)
from aaa.cross_referencer.models import (
    AaaCrossReferenceModel,
    Argument,
    Assignment,
    BooleanLiteral,
    Branch,
    CallArgument,
    CallFunction,
    CallType,
    CallVariable,
    CrossReferencerOutput,
    ForeachLoop,
    Function,
    FunctionBody,
    FunctionBodyItem,
    Identifiable,
    IdentifiablesDict,
    Import,
    IntegerLiteral,
    StringLiteral,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
    UnresolvedFunction,
    UnresolvedImport,
    UnresolvedType,
    UseBlock,
    Variable,
    VariableType,
    WhileLoop,
)
from aaa.parser import models as parser


class CrossReferencer:
    def __init__(self, parser_output: parser.ParserOutput, verbose: bool) -> None:
        self.parsed_files = parser_output.parsed
        self.builtins_path = parser_output.builtins_path
        self.entrypoint = parser_output.entrypoint
        self.identifiers: IdentifiablesDict = {}
        self.exceptions: List[CrossReferenceBaseException] = []
        self.cross_referenced_files: Set[Path] = set()
        self.cross_reference_stack: List[Path] = []
        self.verbose = verbose  # TODO use

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

    def _get_remaining_dependencies(self, file: Path) -> List[Path]:
        deps: List[Path] = []

        if file != self.builtins_path:
            deps += [self.builtins_path]

        deps += self.parsed_files[file].dependencies()

        # NOTE: don't use set difference to maintain import order as in source file
        remaining_deps: List[Path] = []

        for dep in deps:
            if dep not in self.cross_referenced_files and dep not in remaining_deps:
                remaining_deps.append(dep)

        return remaining_deps

    def _cross_reference_file(self, file: Path) -> None:
        if file in self.cross_reference_stack:
            raise CircularDependencyError(self.cross_reference_stack + [file])

        self.cross_reference_stack.append(file)

        for dependency in self._get_remaining_dependencies(file):
            self._cross_reference_file(dependency)

        imports, types, functions = self._load_identifiers(file)

        for import_ in imports:
            self._resolve(import_)

        for type in types:
            self._resolve(type)

        for function in functions:
            self._resolve(function)

        self._resolve_function_bodies(functions)

        self.cross_reference_stack.pop()
        self.cross_referenced_files.add(file)

    def _resolve(
        self, unresolved: UnresolvedImport | UnresolvedType | UnresolvedFunction
    ) -> None:

        resolvers = {
            UnresolvedImport: self._resolve_import,
            UnresolvedType: self._resolve_type,
            UnresolvedFunction: self._resolve_function_signature,
        }

        try:
            identifiable = resolvers[type(unresolved)](unresolved)
        except CrossReferenceBaseException as e:
            self.exceptions.append(e)
        else:
            self._save_identifier(identifiable)

    def _resolve_function_signature(
        self, unresolved: AaaCrossReferenceModel
    ) -> Function:
        assert isinstance(unresolved, UnresolvedFunction)

        params = self._resolve_function_params(unresolved)
        arguments = self._resolve_function_arguments(unresolved, params)
        return_types = self._resolve_function_return_types(unresolved, params)
        function = Function(unresolved, params, arguments, return_types)
        self._check_function_identifiers_collision(function)

        return function

    def print_values(self) -> None:  # pragma: nocover
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

    def _resolve_import(self, import_: AaaCrossReferenceModel) -> Import:
        assert isinstance(import_, UnresolvedImport)

        key = (import_.source_file, import_.source_name)

        try:
            source = self.identifiers[key]
        except KeyError:
            raise ImportedItemNotFound(import_)

        if isinstance(source, Import):
            raise IndirectImportException(import_)

        return Import(import_, source)

    def _get_identifiable(self, identifier: parser.Identifier) -> Identifiable:
        return self._get_identifiable_generic(identifier.name, identifier.position)

    def _get_type(self, identifier: parser.Identifier) -> Type:
        type = self._get_identifiable(identifier)
        assert isinstance(type, Type)
        return type

    def _get_identifiable_generic(self, name: str, position: Position) -> Identifiable:

        builtins_key = (self.builtins_path, name)
        key = (position.file, name)

        if builtins_key in self.identifiers:
            found = self.identifiers[builtins_key]
        elif key in self.identifiers:
            found = self.identifiers[key]
        else:
            raise UnknownIdentifier(position, name)

        if isinstance(found, Import):
            assert not isinstance(found.source, Import)
            return found.source

        return found

    def _resolve_type_field(self, parsed_field: parser.TypeLiteral) -> VariableType:

        type_identifier = parsed_field.identifier
        field_type = self._get_type(type_identifier)

        params: List[VariableType] = []

        for parsed_param in parsed_field.params:
            param_type = self._get_type(parsed_param.identifier)
            assert len(parsed_param.params) == 0

            params.append(
                VariableType(
                    type=param_type,
                    params=[],
                    is_placeholder=False,
                    position=parsed_param.position,
                )
            )

        return VariableType(
            type=field_type,
            params=params,
            is_placeholder=False,
            position=parsed_field.position,
        )

    def _resolve_type(self, unresolved: AaaCrossReferenceModel) -> Type:
        assert isinstance(unresolved, UnresolvedType)
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
            identifier=parsed_arg.identifier,
            var_type=VariableType(
                type=type,
                params=params,
                is_placeholder=arg_type_name in type_params,
                position=parsed_type.position,
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
            params=self._lookup_function_params(type_params, param),
            position=param.position,
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

    def _check_function_identifiers_collision(self, function: Function) -> None:
        for lhs_index, lhs_arg in enumerate(function.arguments):
            for rhs_arg in function.arguments[lhs_index + 1 :]:
                if lhs_arg.name == rhs_arg.name:
                    # Argument names collide
                    raise CollidingIdentifier(lhs_arg, rhs_arg)

        for argument in function.arguments:
            key = (function.position.file, argument.name)
            if key in self.identifiers:
                # Argument collides with file-scoped identifier
                raise CollidingIdentifier(argument, self.identifiers[key])

            if function.name == argument.name:
                # Argument collides with function
                raise CollidingIdentifier(function, argument)

        for param_name, param in function.type_params.items():
            # If a param name collides with file-scoped identifier,
            # creation of the param fails, so it's not tested here.

            if function.name == param_name:
                # Param name collides with function
                raise CollidingIdentifier(function, param)

            for argument in function.arguments:
                # Param name collides with argument
                if param_name == argument.name:
                    raise CollidingIdentifier(param, argument)

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
                    raise InvalidReturnType(type)

                params = self._lookup_function_params(type_params, parsed_return_type)

            return_type = VariableType(
                type=type,
                params=params,
                is_placeholder=return_type_name in type_params,
                position=parsed_return_type.position,
            )

            expected_param_count = return_type.type.param_count
            found_param_count = len(return_type.params)
            if expected_param_count != found_param_count:
                raise UnexpectedTypeParameterCount(
                    return_type.position, expected_param_count, found_param_count
                )

            return_types.append(return_type)
        return return_types

    def _resolve_function_bodies(self, functions: List[UnresolvedFunction]) -> None:
        for unresolved_function in functions:
            key = (unresolved_function.position.file, unresolved_function.name)

            try:
                function = self.identifiers[key]
            except KeyError:
                # Function signature loading failed, so no body to resolve
                continue

            if not isinstance(function, Function):
                # Name collision of function and something else
                continue

            # TODO forward vars everywhere instead of function
            _ = vars

            parsed_body = unresolved_function.parsed.body
            resolver = FunctionBodyResolver(self, function, parsed_body)

            try:
                body = resolver.run()
            except CrossReferenceBaseException as e:
                self.exceptions.append(e)
            else:
                function.body = body


class FunctionBodyResolver:
    def __init__(
        self,
        cross_referencer: CrossReferencer,
        function: Function,
        parsed: parser.FunctionBody,
    ) -> None:
        self.function = function
        self.parsed = parsed
        self.cross_referencer = cross_referencer
        self.vars: Dict[str, Argument | Variable] = {
            arg.name: arg for arg in self.function.arguments
        }

    def run(self) -> FunctionBody:
        return self._resolve_function_body(self.parsed)

    def _resolve_function_body(self, parsed_body: parser.FunctionBody) -> FunctionBody:
        return FunctionBody(
            items=[
                self._resolve_function_body_item(item) for item in parsed_body.items
            ],
            parsed=parsed_body,
        )

    def _resolve_function_type_param(
        self, function: Function, type_literal: parser.TypeLiteral
    ) -> VariableType:
        for param_name, param in function.type_params.items():
            if type_literal.identifier.name == param_name:
                return VariableType(param, [], True, type_literal.position)

        try:
            identifiable = self._get_identifiable_from_type_literal(type_literal)
        except KeyError:
            # TODO unknown type param
            raise NotImplementedError

        if not isinstance(identifiable, Type):
            # Use non-type as type param
            raise NotImplementedError

        return VariableType(identifiable, [], False, type_literal.position)

    def _resolve_branch(self, branch: parser.Branch) -> Branch:
        resolved_else_body: Optional[FunctionBody] = None

        if branch.else_body:
            resolved_else_body = self._resolve_function_body(branch.else_body)

        return Branch(
            condition=self._resolve_function_body(branch.condition),
            if_body=self._resolve_function_body(branch.if_body),
            else_body=resolved_else_body,
            parsed=branch,
        )

    def _resolve_while_loop(self, while_loop: parser.WhileLoop) -> WhileLoop:
        return WhileLoop(
            condition=self._resolve_function_body(while_loop.condition),
            body=self._resolve_function_body(while_loop.body),
            parsed=while_loop,
        )

    def _resolve_function_name(
        self, function_name: parser.FunctionName
    ) -> CallArgument | CallVariable | CallFunction | CallType:

        try:
            var = self.vars[function_name.name()]
        except KeyError:
            pass
        else:
            if function_name.type_params:
                # TODO handle handle case like: fn foo args a as int { a[b] drop }
                # TODO handle handle case like: fn foo { 0 use c { c[b] } }
                raise NotImplementedError

            if isinstance(var, Argument):
                return CallArgument(var, function_name.position)
            elif isinstance(var, Variable):
                return CallVariable(var, function_name.position)
            else:  # pragma: nocover
                assert False

        identifiable = self._get_identifiable_from_function_name(function_name)

        if isinstance(identifiable, Function):
            return CallFunction(
                identifiable,
                [
                    self._resolve_function_type_param(self.function, param)
                    for param in function_name.type_params
                ],
                function_name.position,
            )

        if isinstance(identifiable, Type):
            var_type = VariableType(
                identifiable,
                [
                    self._lookup_function_param(self.function.type_params, param)
                    for param in function_name.type_params
                ],
                False,
                function_name.position,
            )

            expected_param_count = var_type.type.param_count
            found_param_count = len(var_type.params)
            if expected_param_count != found_param_count:
                raise UnexpectedTypeParameterCount(
                    function_name.position, expected_param_count, found_param_count
                )

            return CallType(var_type)

        assert False  # pragma: nocover

    def _resolve_struct_field_update(
        self, update: parser.StructFieldUpdate
    ) -> StructFieldUpdate:
        return StructFieldUpdate(
            parsed=update,
            new_value_expr=self._resolve_function_body(update.new_value_expr),
        )

    def _resolve_function_body_item(
        self, parsed_item: parser.FunctionBodyItem
    ) -> FunctionBodyItem:
        if isinstance(parsed_item, parser.IntegerLiteral):
            return IntegerLiteral(parsed_item)
        elif isinstance(parsed_item, parser.StringLiteral):
            return StringLiteral(parsed_item)
        elif isinstance(parsed_item, parser.BooleanLiteral):
            return BooleanLiteral(parsed_item)
        elif isinstance(parsed_item, parser.WhileLoop):
            return self._resolve_while_loop(parsed_item)
        elif isinstance(parsed_item, parser.Branch):
            return self._resolve_branch(parsed_item)
        elif isinstance(parsed_item, parser.FunctionName):
            return self._resolve_function_name(parsed_item)
        elif isinstance(parsed_item, parser.StructFieldQuery):
            return StructFieldQuery(parsed_item)
        elif isinstance(parsed_item, parser.StructFieldUpdate):
            return self._resolve_struct_field_update(parsed_item)
        elif isinstance(parsed_item, parser.ForeachLoop):
            return self._resolve_foreach_loop(parsed_item)
        elif isinstance(parsed_item, parser.Assignment):
            return self._resolve_assignment(parsed_item)
        elif isinstance(parsed_item, parser.UseBlock):
            return self._resolve_use_block(parsed_item)
        else:  # pragma: nocover
            assert False

    def _resolve_assignment(self, parsed: parser.Assignment) -> Assignment:
        body = self._resolve_function_body(parsed.body)
        variables = [Variable(var) for var in parsed.variables]
        return Assignment(parsed, variables, body)

    def _resolve_use_block(self, parsed: parser.UseBlock) -> UseBlock:
        # TODO mark variables somehow such that they can be used in body
        body = self._resolve_function_body(parsed.body)
        variables = [Variable(var) for var in parsed.variables]
        return UseBlock(parsed, variables, body)

    def _resolve_foreach_loop(self, parsed: parser.ForeachLoop) -> ForeachLoop:
        body = self._resolve_function_body(parsed.body)
        return ForeachLoop(parsed, body)

    def _get_identifiable_from_function_name(
        self, func_name: parser.FunctionName
    ) -> Identifiable:
        return self._get_identifiable_generic(func_name.name(), func_name.position)

    def _get_identifiable_from_type_literal(
        self, type: parser.TypeLiteral
    ) -> Identifiable:
        return self._get_identifiable_generic(type.identifier.name, type.position)

    def _get_identifiable_generic(self, name: str, position: Position) -> Identifiable:
        return self.cross_referencer._get_identifiable_generic(name, position)

    def _lookup_function_param(
        self, type_params: Dict[str, Type], param: parser.TypeLiteral
    ) -> VariableType:
        return self.cross_referencer._lookup_function_param(type_params, param)

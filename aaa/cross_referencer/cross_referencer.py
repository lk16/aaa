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
    InvalidCallWithTypeParameters,
    InvalidEnumType,
    InvalidEnumVariant,
    InvalidReturnType,
    InvalidType,
    UnexpectedTypeParameterCount,
    UnknownIdentifier,
    UnknownVariable,
)
from aaa.cross_referencer.models import (
    Argument,
    Assignment,
    BooleanLiteral,
    Branch,
    CallFunction,
    CallType,
    CallVariable,
    CaseBlock,
    CrossReferencerOutput,
    DefaultBlock,
    ForeachLoop,
    Function,
    FunctionBody,
    FunctionBodyItem,
    Identifiable,
    IdentifiablesDict,
    Import,
    IntegerLiteral,
    MatchBlock,
    Never,
    Return,
    StringLiteral,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
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
        self.verbose = verbose

    def _save_identifier(self, identifiable: Identifiable) -> None:
        key = identifiable.identify()

        try:
            found = self.identifiers[key]
        except KeyError:
            self.identifiers[key] = identifiable
        else:
            self.exceptions += [CollidingIdentifier([identifiable, found])]

    def run(self) -> CrossReferencerOutput:
        self._cross_reference_file(self.entrypoint)

        if self.exceptions:
            raise AaaRunnerException(self.exceptions)

        self._print_values()

        output = CrossReferencerOutput(
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

        for type in output.types.values():
            assert type.is_resolved()

        for function in output.functions.values():
            assert function.is_resolved()

        # TODO check if imports are resolved

        return output

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

        for type in types:
            self._save_identifier(type)

        for function in functions:
            self._save_identifier(function)

        for import_ in imports:
            self._save_identifier(import_)

        # TODO wrap all calls to self._resolve_* functions in try except for CrossReferenceBaseException

        for import_ in imports:
            self._resolve_import(import_)

        for type in types:
            self._resolve_type(type)

        for function in functions:
            self._resolve_function_signature(function)

        for function in functions:
            self._resolve_function_body(function)

        self.cross_reference_stack.pop()
        self.cross_referenced_files.add(file)

    def _resolve_function_signature(self, function: Function) -> None:
        params = self._resolve_function_params(function)
        arguments = self._resolve_function_arguments(function, params)
        return_types = self._resolve_function_return_types(function, params)

        is_enum_ctor = False

        # TODO Find a better way to detect enum ctors
        try:
            enum_type = self._get_identifiable_generic(
                function.struct_name, function.position
            )
        except UnknownIdentifier:
            pass
        else:
            if isinstance(enum_type, Type):
                is_enum_ctor = function.func_name in enum_type.enum_fields

        parsed_body = function.get_unresolved().parsed.body

        function.add_signature(
            parsed_body, params, arguments, return_types, is_enum_ctor
        )
        self._check_function_identifiers_collision(function)

    def _print_values(self) -> None:  # pragma: nocover
        if not self.verbose:
            return

        for (_, identifier), identifiable in self.identifiers.items():

            if isinstance(identifiable, Function):
                file = identifiable.position.short_filename()
                prefix = f"cross_referencer | Function {file}:{identifier}"

                print(prefix)

                for arg in identifiable.arguments:
                    file = arg.var_type.position.short_filename()
                    name = arg.name
                    var_type = arg.var_type

                    if arg.var_type.is_placeholder:
                        print(f"{prefix} | Argument {name} of type {var_type}")
                    else:
                        print(f"{prefix} | Argument {name} of type {file}:{var_type}")

                if isinstance(identifiable.return_types, Never):
                    print(f"{prefix} | Return type never")
                elif isinstance(identifiable.return_types, list):

                    for return_type in identifiable.return_types:
                        file = return_type.type.position.short_filename()

                        if return_type.is_placeholder:
                            print(f"{prefix} | Return type {return_type}")
                        else:
                            print(f"{prefix} | Return type {file}:{return_type}")
                else:
                    assert False

            elif isinstance(identifiable, Type):
                file = identifiable.position.short_filename()
                prefix = f"cross_referencer | Type {file}:{identifier}"

                print(prefix)

                for name, var_type in identifiable.fields.items():
                    file = var_type.position.short_filename()
                    print(f"{prefix} | Field {name} of type {file}:{var_type}")

            elif isinstance(identifiable, Import):
                file = identifiable.position.short_filename()
                prefix = f"cross_referencer | Import {file}:{identifier}"
                source_type = type(identifiable.source).__name__

                print(
                    f"{prefix} | Import {source_type} from {identifiable.source_file}:{identifiable.source_name}"
                )

            else:  # pragma: nocover
                raise NotImplementedError

    def _load_identifiers(
        self, file: Path
    ) -> Tuple[List[Import], List[Type], List[Function]]:
        imports: List[Import] = []
        functions: List[Function] = []
        types: List[Type] = []

        parsed_file = self.parsed_files[file]

        types += self._load_types(parsed_file.types)
        types += self._load_struct_types(parsed_file.structs)

        enum_funcs, enum_types = self._load_enums(parsed_file.enums)
        types += enum_types
        functions += enum_funcs

        functions += self._load_functions(parsed_file.functions)
        imports += self._load_imports(parsed_file.imports)
        return imports, types, functions

    def _load_enums(
        self, parsed_enums: List[parser.Enum]
    ) -> Tuple[List[Function], List[Type]]:
        functions: List[Function] = []
        types: List[Type] = []

        for parsed_enum in parsed_enums:
            dummy_position = Position(parsed_enum.position.file, -1, -1)

            type = Type(parsed_enum, 0)
            types.append(type)

            for variant in parsed_enum.variants:
                parsed_function = parser.Function(
                    position=dummy_position,
                    struct_name=parsed_enum.identifier,
                    func_name=variant.name,
                    type_params=[],
                    arguments=[
                        parser.Argument(
                            identifier=parser.Identifier(dummy_position, "_"),
                            type=variant.type,
                        )
                    ],
                    return_types=[
                        parser.TypeLiteral(
                            position=parsed_enum.position,
                            identifier=parsed_enum.identifier,
                            params=[],
                            const=False,
                        )
                    ],
                    body=None,
                )

                function = Function(parsed_function)
                functions.append(function)

        return functions, types

    def _load_struct_types(self, parsed_structs: List[parser.Struct]) -> List[Type]:
        return [Type(parsed_struct, 0) for parsed_struct in parsed_structs]

    def _load_functions(
        self, parsed_functions: List[parser.Function]
    ) -> List[Function]:
        return [Function(parsed_function) for parsed_function in parsed_functions]

    def _load_imports(self, parsed_imports: List[parser.Import]) -> List[Import]:
        imports: List[Import] = []

        for parsed_import in parsed_imports:
            for imported_item in parsed_import.imported_items:
                import_ = Import(imported_item, parsed_import)
                imports.append(import_)

        return imports

    def _load_types(self, types: List[parser.TypeLiteral]) -> List[Type]:
        return [Type(type, len(type.params)) for type in types]

    def _resolve_import(self, import_: Import) -> None:
        key = (import_.source_file, import_.source_name)

        try:
            source = self.identifiers[key]
        except KeyError:
            raise ImportedItemNotFound(import_)

        if isinstance(source, Import):
            raise IndirectImportException(import_)

        return import_.resolve(source)

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
                    is_const=False,
                )
            )

        return VariableType(
            type=field_type,
            params=params,
            is_placeholder=False,
            position=parsed_field.position,
            is_const=False,
        )

    def _resolve_type(self, type: Type) -> None:
        fields = {
            field_name: self._resolve_type_field(parsed_field)
            for field_name, parsed_field in type.get_unresolved().parsed_field_types.items()
        }

        enum_variants: Dict[str, Tuple[VariableType, int]] = {}
        for variant_name, (
            variant_type,
            variariant_id,
        ) in type.get_unresolved().parsed_variants.items():
            enum_variants[variant_name] = (
                self._resolve_type_field(variant_type),
                variariant_id,
            )

        type.resolve(fields, enum_variants, type.param_count)

    def _resolve_function_param(
        self, function: Function, parsed_type_param: parser.TypeLiteral
    ) -> Type:
        param_name = parsed_type_param.identifier.name
        type_literal: Optional[parser.TypeLiteral] = None

        for param in function.get_unresolved().parsed.type_params:
            if param.identifier.name == param_name:
                type_literal = param

        assert type_literal

        type = Type(type_literal, 0)

        if (function.position.file, param_name) in self.identifiers:
            # Another identifier in the same file has this name.
            colliding_identifier = self.identifiers[
                (function.position.file, param_name)
            ]
            raise CollidingIdentifier([type, colliding_identifier])

        return type

    def _resolve_function_params(self, function: Function) -> Dict[str, Type]:
        return {
            parsed_type_param.identifier.name: self._resolve_function_param(
                function, parsed_type_param
            )
            for parsed_type_param in function.get_unresolved().parsed.type_params
        }

    def _resolve_function_argument(
        self,
        function: Function,
        type_params: Dict[str, Type],
        parsed_arg: parser.Argument,
    ) -> Argument:
        parsed_type = parsed_arg.type
        arg_type_name = parsed_arg.type.identifier.name
        type: Identifiable

        found_type_param: Optional[parser.TypeLiteral] = None
        for type_param in function.get_unresolved().parsed.type_params:
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
                is_const=parsed_type.const,
            ),
        )

    def _resolve_function_arguments(
        self, function: Function, type_params: Dict[str, Type]
    ) -> List[Argument]:
        return [
            self._resolve_function_argument(function, type_params, parsed_arg)
            for parsed_arg in function.get_unresolved().parsed.arguments
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
            is_const=param.const,
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
                    raise CollidingIdentifier([lhs_arg, rhs_arg])

        for argument in function.arguments:
            key = (function.position.file, argument.name)
            if key in self.identifiers:
                identifier = self.identifiers[key]
                # Argument collides with file-scoped identifier
                raise CollidingIdentifier([identifier, argument])

            if function.name == argument.name:
                # Argument collides with function
                raise CollidingIdentifier([function, argument])

        for param_name, param in function.type_params.items():
            # If a param name collides with file-scoped identifier,
            # creation of the param fails, so it's not tested here.

            if function.name == param_name:
                # Param name collides with function
                raise CollidingIdentifier([function, param])

            for argument in function.arguments:
                # Param name collides with argument
                if param_name == argument.name:
                    raise CollidingIdentifier([param, argument])

    def _resolve_function_return_types(
        self, function: Function, type_params: Dict[str, Type]
    ) -> List[VariableType] | Never:

        parsed_return_types = function.get_unresolved().parsed.return_types

        if isinstance(parsed_return_types, parser.Never):
            return Never()

        return_types: List[VariableType] = []

        for parsed_return_type in parsed_return_types:
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
                is_const=parsed_return_type.const,
            )

            expected_param_count = return_type.type.param_count
            found_param_count = len(return_type.params)
            if expected_param_count != found_param_count:
                raise UnexpectedTypeParameterCount(
                    return_type.position, expected_param_count, found_param_count
                )

            return_types.append(return_type)
        return return_types

    def _resolve_function_body(self, function: Function) -> None:
        parsed_body = function.get_with_signature().parsed_body

        if not parsed_body:
            function.resolve(None)
            return

        resolver = FunctionBodyResolver(self, function, parsed_body)

        try:
            body = resolver.run()
        except CrossReferenceBaseException as e:
            self.exceptions.append(e)
        else:
            function.resolve(body)


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

    def _resolve_call(
        self, call: parser.Call
    ) -> CallVariable | CallFunction | CallType:

        try:
            var = self.vars[call.name()]
        except KeyError:
            pass
        else:
            if call.type_params:
                # Handles cases like:
                # fn foo { 0 use c { c[b] } }
                # fn foo args a as int { a[b] drop }
                raise InvalidCallWithTypeParameters(call, var)

            return CallVariable(var.name, call.position)

        identifiable = self._get_identifiable_from_call(call)

        if isinstance(identifiable, Function):
            assert not call.type_params

            return CallFunction(
                identifiable,
                [],
                call.position,
            )

        if isinstance(identifiable, Type):
            var_type = VariableType(
                identifiable,
                [
                    self._lookup_function_param(self.function.type_params, param)
                    for param in call.type_params
                ],
                False,
                call.position,
                False,
            )

            expected_param_count = var_type.type.param_count
            found_param_count = len(var_type.params)
            if expected_param_count != found_param_count:
                raise UnexpectedTypeParameterCount(
                    call.position, expected_param_count, found_param_count
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
        elif isinstance(parsed_item, parser.Call):
            return self._resolve_call(parsed_item)
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
        elif isinstance(parsed_item, parser.MatchBlock):
            return self._resolve_match_block(parsed_item)
        elif isinstance(parsed_item, parser.Return):
            return self._resolve_return(parsed_item)
        else:  # pragma: nocover
            assert False

    def _resolve_match_block(self, parsed: parser.MatchBlock) -> MatchBlock:
        blocks: List[CaseBlock | DefaultBlock] = []

        for block in parsed.blocks:
            if isinstance(block, parser.CaseBlock):
                blocks.append(self._resolve_case_block(block))
            elif isinstance(block, parser.DefaultBlock):
                blocks.append(self._resolve_default_block(block))
            else:  # pragma: nocover
                assert False

        return MatchBlock(parsed.position, blocks)

    def _resolve_case_block(self, parsed: parser.CaseBlock) -> CaseBlock:
        enum_type_name = parsed.enum_name
        variant_name = parsed.enum_variant_name.name
        assert enum_type_name  # parser ensures this doesn't fail

        enum_type = self._get_identifiable_generic(enum_type_name.name, parsed.position)

        if not isinstance(enum_type, Type):
            raise InvalidEnumType(parsed.position, enum_type)

        if not enum_type.enum_fields:
            raise InvalidEnumType(parsed.position, enum_type)

        if variant_name not in enum_type.enum_fields:
            raise InvalidEnumVariant(parsed.position, enum_type, variant_name)

        return CaseBlock(
            parsed.position,
            enum_type=enum_type,
            variant_name=variant_name,
            body=self._resolve_function_body(parsed.body),
        )

    def _resolve_default_block(self, parsed: parser.DefaultBlock) -> DefaultBlock:
        return DefaultBlock(parsed.position, self._resolve_function_body(parsed.body))

    def _resolve_return(self, parsed: parser.Return) -> Return:
        return Return(parsed)

    def _resolve_assignment(self, parsed: parser.Assignment) -> Assignment:
        variables = [Variable(var, False) for var in parsed.variables]

        for var in variables:
            if var.name not in self.vars:
                raise UnknownVariable(var)

        body = self._resolve_function_body(parsed.body)
        return Assignment(parsed, variables, body)

    def _resolve_use_block(self, parsed: parser.UseBlock) -> UseBlock:
        variables = [Variable(parsed_var, False) for parsed_var in parsed.variables]

        for var in variables:
            if var.name in self.vars:
                colliding_var = self.vars[var.name]
                raise CollidingIdentifier([var, colliding_var])

            try:
                identifiable = self._get_identifiable_generic(var.name, var.position)
            except UnknownIdentifier:
                pass
            else:
                raise CollidingIdentifier([var, identifiable])

            self.vars[var.name] = var

        body = self._resolve_function_body(parsed.body)

        for var in variables:
            del self.vars[var.name]

        return UseBlock(parsed, variables, body)

    def _resolve_foreach_loop(self, parsed: parser.ForeachLoop) -> ForeachLoop:
        body = self._resolve_function_body(parsed.body)
        return ForeachLoop(parsed, body)

    def _get_identifiable_from_call(self, call: parser.Call) -> Identifiable:
        return self._get_identifiable_generic(call.name(), call.position)

    def _get_identifiable_generic(self, name: str, position: Position) -> Identifiable:
        return self.cross_referencer._get_identifiable_generic(name, position)

    def _lookup_function_param(
        self, type_params: Dict[str, Type], param: parser.TypeLiteral
    ) -> VariableType:
        return self.cross_referencer._lookup_function_param(type_params, param)

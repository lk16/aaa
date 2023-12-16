from pathlib import Path
from typing import Callable, Dict, List, Set, Tuple, Type

from basil.models import Position

from aaa.cross_referencer.exceptions import (
    CircularDependencyError,
    CollidingEnumVariant,
    CollidingIdentifier,
    CrossReferenceBaseException,
    FunctionPointerTargetNotFound,
    ImportedItemNotFound,
    IndirectImportException,
    InvalidArgument,
    InvalidEnumType,
    InvalidEnumVariant,
    InvalidFunctionPointerTarget,
    InvalidReturnType,
    InvalidType,
    UnexpectedBuiltin,
    UnexpectedTypeParameterCount,
    UnknownIdentifier,
)
from aaa.cross_referencer.models import (
    Argument,
    Assignment,
    BooleanLiteral,
    Branch,
    CallEnumConstructor,
    CallFunction,
    CallFunctionByPointer,
    CallType,
    CallVariable,
    CaseBlock,
    CharacterLiteral,
    CrossReferencerOutput,
    DefaultBlock,
    Enum,
    EnumConstructor,
    ForeachLoop,
    Function,
    FunctionBody,
    FunctionBodyItem,
    FunctionPointer,
    GetFunctionPointer,
    Identifiable,
    IdentifiablesDict,
    ImplicitEnumConstructorImport,
    ImplicitFunctionImport,
    Import,
    IntegerLiteral,
    MatchBlock,
    Never,
    Return,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    UseBlock,
    Variable,
    VariableType,
    WhileLoop,
)
from aaa.parser import models as parser
from aaa.runner.exceptions import AaaTranslationException


class CrossReferencer:
    def __init__(self, parser_output: parser.ParserOutput, verbose: bool) -> None:
        self.parsed_files = parser_output.parsed
        self.builtins_path = parser_output.builtins_path
        self.entrypoint = parser_output.entrypoint
        self.identifiers: IdentifiablesDict = {}
        self.exceptions: List[CrossReferenceBaseException] = []
        self.cross_referenced_files: Set[Path] = set()
        self.dependency_stack: List[Path] = []
        self.verbose = verbose

    def _save_identifier(self, identifiable: Identifiable) -> None:
        key = identifiable.identify()

        try:
            found = self.identifiers[key]
        except KeyError:
            self.identifiers[key] = identifiable
        else:
            if found.position == identifiable.position:
                # Cannot collide with same item
                return

            self.exceptions += [CollidingIdentifier([identifiable, found])]

    def run(self) -> CrossReferencerOutput:
        try:
            self._cross_reference_file(self.entrypoint)
        except CrossReferenceBaseException as e:
            self.exceptions.append(e)

        if self.exceptions:
            raise AaaTranslationException(self.exceptions)

        self._print_values()

        output = CrossReferencerOutput(
            functions={
                k: v for (k, v) in self.identifiers.items() if isinstance(v, Function)
            },
            enums={k: v for (k, v) in self.identifiers.items() if isinstance(v, Enum)},
            structs={
                k: v for (k, v) in self.identifiers.items() if isinstance(v, Struct)
            },
            imports={
                k: v for (k, v) in self.identifiers.items() if isinstance(v, Import)
            },
            builtins_path=self.builtins_path,
            entrypoint=self.entrypoint,
        )

        return output

    def _get_remaining_dependencies(self, file: Path) -> List[Path]:
        deps: List[Path] = []

        if file != self.builtins_path:
            deps += [self.builtins_path]

        deps += self.parsed_files[file].get_dependencies()

        # NOTE: don't use set difference to maintain import order as in source file
        remaining_deps: List[Path] = []

        for dep in deps:
            if dep not in self.cross_referenced_files and dep not in remaining_deps:
                remaining_deps.append(dep)

        return remaining_deps

    def _get_implicit_function_imports(self, import_: Import) -> IdentifiablesDict:
        if not import_.is_resolved():
            return {}

        source = import_.resolved().source
        implicit_imports: Dict[Tuple[Path, str], Identifiable] = {}

        if isinstance(source, Struct):
            for (file, name), identifier in self.identifiers.items():
                if source.position.file == file and name.startswith(source.name + ":"):
                    assert isinstance(identifier, Function)
                    implicit_imports[
                        (import_.position.file, name)
                    ] = ImplicitFunctionImport(identifier)

        if isinstance(source, Enum):
            for (file, name), identifier in self.identifiers.items():
                if source.position.file == file and name.startswith(source.name + ":"):
                    key = (import_.position.file, name)
                    if isinstance(identifier, EnumConstructor):
                        implicit_imports[key] = ImplicitEnumConstructorImport(
                            identifier
                        )
                    elif isinstance(identifier, Function):
                        implicit_imports[key] = ImplicitFunctionImport(identifier)

        return implicit_imports

    def _cross_reference_file(self, file: Path) -> None:
        if file in self.dependency_stack:
            raise CircularDependencyError(self.dependency_stack + [file])

        self.dependency_stack.append(file)

        for dependency in self._get_remaining_dependencies(file):
            self._cross_reference_file(dependency)

        imports, structs, enums, enum_ctors, functions = self._load_identifiers(file)

        for identifier in imports + structs + enums + enum_ctors + functions:
            self._save_identifier(identifier)

        for import_ in imports:
            self._resolve_import(import_)
            implicit_imports = self._get_implicit_function_imports(import_)
            self.identifiers.update(implicit_imports)

        for type in structs:
            self._resolve_struct(type)

        for enum in enums:
            self._resolve_enum(enum)

        for function in functions:
            self._resolve_function_signature(function)

        for function in functions:
            if not isinstance(function.state, Function.WithSignature):
                continue
            self._resolve_function_body(function)

        self.dependency_stack.pop()
        self.cross_referenced_files.add(file)

    def _resolve_function_signature(self, function: Function) -> None:
        try:
            params = self._resolve_function_params(function)
            arguments = self._resolve_function_arguments(function, params)
            return_types = self._resolve_function_return_types(function, params)
            parsed_body = function.get_unresolved().parsed.get_body()

            function.add_signature(parsed_body, params, arguments, return_types)
            self._check_function_identifiers_collision(function)
        except CrossReferenceBaseException as e:
            self.exceptions.append(e)

    def _print_values(self) -> None:  # pragma: nocover
        if not self.verbose:
            return

        for (_, identifier), identifiable in self.identifiers.items():
            if isinstance(identifiable, Function):
                file = identifiable.position.file
                prefix = f"cross_referencer | Function {file}:{identifier}"

                print(prefix)

                for arg in identifiable.arguments:
                    file = arg.type.position.file
                    name = arg.name
                    var_type = arg.type

                    if isinstance(arg.type, FunctionPointer):
                        print(f"{prefix} | Argument {name} of type ptr to function")
                    elif arg.type.is_placeholder:
                        print(f"{prefix} | Argument {name} of type {var_type}")
                    else:
                        print(f"{prefix} | Argument {name} of type {file}:{var_type}")

                if isinstance(identifiable.return_types, Never):
                    print(f"{prefix} | Return type never")
                else:
                    for return_type in identifiable.return_types:
                        if isinstance(return_type, FunctionPointer):
                            print(f"{prefix} | Return type ptr to function")
                        elif return_type.is_placeholder:
                            print(f"{prefix} | Return type {return_type}")
                        else:
                            file = return_type.type.position.file
                            print(f"{prefix} | Return type {file}:{return_type}")

            elif isinstance(identifiable, Struct):
                file = identifiable.position.file
                prefix = f"cross_referencer | Type {file}:{identifier}"

                print(prefix)

                for name, var_type in identifiable.fields.items():
                    file = var_type.position.file
                    print(f"{prefix} | Field {name} of type {file}:{var_type}")

            elif isinstance(identifiable, Import):
                file = identifiable.position.file
                prefix = f"cross_referencer | Import {file}:{identifier}"
                source_type = type(identifiable.source).__name__

                print(
                    f"{prefix} | Import {source_type} from {identifiable.source_file}:{identifiable.source_name}"
                )

            elif isinstance(
                identifiable,
                (
                    Enum,
                    EnumConstructor,
                    ImplicitFunctionImport,
                    ImplicitEnumConstructorImport,
                ),
            ):
                pass  # TODO #171 Redo verbose mode for cross referencer

            else:  # pragma: nocover
                raise NotImplementedError

    def _load_identifiers(
        self, file: Path
    ) -> Tuple[
        List[Import], List[Struct], List[Enum], List[EnumConstructor], List[Function]
    ]:
        parsed_file = self.parsed_files[file]

        structs = self._load_struct_types(parsed_file.structs)
        enum_ctors, enums = self._load_enums(parsed_file.enums)

        functions = self._load_functions(parsed_file.functions)
        imports = self._load_imports(parsed_file.imports)
        return imports, structs, enums, enum_ctors, functions

    def _load_enums(
        self, parsed_enums: List[parser.Enum]
    ) -> Tuple[List[EnumConstructor], List[Enum]]:
        enum_ctors: List[EnumConstructor] = []
        enums: List[Enum] = []

        for parsed_enum in parsed_enums:
            enum = Enum(parsed_enum, 0)
            enums.append(enum)

            variants: Dict[str, parser.EnumVariant] = {}
            for variant in parsed_enum.get_variants():
                try:
                    found = variants[variant.name.value]
                except KeyError:
                    pass
                else:
                    raise CollidingEnumVariant(parsed_enum, [variant, found])

                variants[variant.name.value] = variant

            enum_ctors += [
                EnumConstructor(enum, variant.name.value)
                for variant in parsed_enum.get_variants()
            ]

        return enum_ctors, enums

    def _load_struct_types(self, parsed_structs: List[parser.Struct]) -> List[Struct]:
        structs: List[Struct] = []

        for parsed_struct in parsed_structs:
            fields = parsed_struct.get_fields()

            if fields is None:
                if parsed_struct.position.file != self.builtins_path:
                    raise UnexpectedBuiltin(parsed_struct.position)
                fields = {}

            structs.append(Struct.from_parsed_struct(parsed_struct, fields))

        return structs

    def _load_functions(
        self, parsed_functions: List[parser.Function]
    ) -> List[Function]:
        return [Function(parsed_function) for parsed_function in parsed_functions]

    def _load_imports(self, parsed_imports: List[parser.Import]) -> List[Import]:
        imports: List[Import] = []

        for parsed_import in parsed_imports:
            for imported_item in parsed_import.imported_items.value:
                import_ = Import(imported_item, parsed_import)
                imports.append(import_)

        return imports

    def _resolve_import(self, import_: Import) -> None:
        key = (import_.source_file, import_.source_name)

        try:
            source = self.identifiers[key]
        except KeyError:
            e: CrossReferenceBaseException = ImportedItemNotFound(import_)
            self.exceptions.append(e)
            return

        if isinstance(source, Import):
            e = IndirectImportException(import_)
            self.exceptions.append(e)
            return

        return import_.resolve(source)

    def _get_identifiable(self, identifier: parser.Identifier) -> Identifiable:
        return self._get_identifiable_generic(identifier.value, identifier.position)

    def _get_type(self, identifier: parser.Identifier) -> Struct | Enum:
        type = self._get_identifiable(identifier)
        assert isinstance(type, (Struct, Enum))
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
            if not isinstance(found.state, Import.Resolved):
                # Something went wrong resolving the import earlier, so we can't proceed.
                raise UnknownIdentifier(position, name)

            assert not isinstance(found.source, Import)
            return found.source

        return found

    def _resolve_type(
        self, parsed: parser.TypeLiteral | parser.FunctionPointerTypeLiteral
    ) -> VariableType | FunctionPointer:
        if isinstance(parsed, parser.FunctionPointerTypeLiteral):
            parsed_return_types = parsed.get_return_types()
            if isinstance(parsed_return_types, parser.Never):
                return_types: List[VariableType | FunctionPointer] | Never = Never()
            else:
                return_types = [
                    self._resolve_type(type) for type in parsed_return_types
                ]

            return FunctionPointer(
                parsed.position,
                argument_types=[
                    self._resolve_type(type) for type in parsed.get_arguments()
                ],
                return_types=return_types,
            )

        type_identifier = parsed.identifier
        field_type = self._get_type(type_identifier)

        params: List[VariableType | FunctionPointer] = []

        for parsed_param in parsed.get_params():
            if isinstance(parsed_param, parser.TypeLiteral):
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
            else:
                assert isinstance(parsed_param, parser.FunctionPointerTypeLiteral)
                params.append(self._resolve_type(parsed_param))

        return VariableType(
            type=field_type,
            params=params,
            is_placeholder=False,
            position=parsed.position,
            is_const=False,
        )

    def _resolve_struct_params(self, struct: Struct) -> Dict[str, Struct]:
        resolved_params: Dict[str, Struct] = {}

        for parsed_type_param in struct.get_unresolved().parsed_params:
            struct = Struct.from_identifier(parsed_type_param)
            param_name = parsed_type_param.value

            try:
                colliding = self.identifiers[(struct.position.file, param_name)]
            except KeyError:
                pass
            else:
                raise CollidingIdentifier([struct, colliding])

            resolved_params[param_name] = struct

        return resolved_params

    def _resolve_struct_field(
        self,
        struct: Struct,
        type_params: Dict[str, Struct],
        parsed_field_type: parser.TypeLiteral | parser.FunctionPointerTypeLiteral,
    ) -> VariableType | FunctionPointer:
        if isinstance(parsed_field_type, parser.FunctionPointerTypeLiteral):
            return self._resolve_type(parsed_field_type)

        assert isinstance(parsed_field_type, parser.TypeLiteral)
        arg_type_name = parsed_field_type.identifier.value

        params: List[VariableType | FunctionPointer] = []

        try:
            field_type: Struct | Enum = type_params[arg_type_name]
        except KeyError:
            identifiable = self._get_identifiable(parsed_field_type.identifier)

            if not isinstance(identifiable, (Enum, Struct)):
                raise InvalidArgument(used=parsed_field_type, found=identifiable)

            field_type = identifiable

            if len(parsed_field_type.params) != field_type.param_count:
                raise UnexpectedTypeParameterCount(
                    position=parsed_field_type.identifier.position,
                    expected_param_count=field_type.param_count,
                    found_param_count=len(parsed_field_type.params),
                )

            params = self._lookup_function_params(type_params, parsed_field_type)

        return VariableType(
            type=field_type,
            params=params,
            is_placeholder=arg_type_name in type_params,
            position=parsed_field_type.position,
            is_const=parsed_field_type.const,
        )

    def _resolve_struct(self, struct: Struct) -> None:
        parsed_field_types = struct.get_unresolved().parsed_field_types
        resolved_params = self._resolve_struct_params(struct)

        fields = {
            field_name: self._resolve_struct_field(
                struct, resolved_params, parsed_field
            )
            for field_name, parsed_field in parsed_field_types.items()
        }

        struct.resolve(resolved_params, fields)

    def _resolve_enum(self, enum: Enum) -> None:
        parsed_variants = enum.get_unresolved().parsed_variants

        enum_variants: Dict[str, List[VariableType | FunctionPointer]] = {}
        for variant_name, associated_data in parsed_variants.items():
            try:
                resolved_associated_data = [
                    self._resolve_type(item) for item in associated_data
                ]
            except CrossReferenceBaseException as e:
                self.exceptions.append(e)
                continue

            enum_variants[variant_name] = resolved_associated_data

        enum.resolve(enum_variants)

    def _resolve_function_params(self, function: Function) -> Dict[str, Struct]:
        resolved_params: Dict[str, Struct] = {}

        for parsed_type_param in function.get_unresolved().parsed.get_params():
            struct = Struct.from_identifier(parsed_type_param)
            param_name = parsed_type_param.value

            try:
                colliding = self.identifiers[(function.position.file, param_name)]
            except KeyError:
                pass
            else:
                raise CollidingIdentifier([struct, colliding])

            resolved_params[param_name] = struct

        return resolved_params

    def _resolve_function_argument(
        self,
        type_params: Dict[str, Struct],
        parsed_arg: parser.Argument,
    ) -> Argument:
        parsed_type = parsed_arg.type.literal
        arg_type: VariableType | FunctionPointer

        if isinstance(parsed_type, parser.FunctionPointerTypeLiteral):
            arg_type = self._resolve_type(parsed_type)
            return Argument(identifier=parsed_arg.identifier, type=arg_type)

        assert isinstance(parsed_type, parser.TypeLiteral)
        arg_type_name = parsed_type.identifier.value
        type: Identifiable

        params: List[VariableType | FunctionPointer] = []

        try:
            type = type_params[arg_type_name]
        except KeyError:
            type = self._get_identifiable(parsed_type.identifier)

            if not isinstance(type, (Enum, Struct)):
                raise InvalidArgument(used=parsed_type, found=type)

            if len(parsed_type.params) != type.param_count:
                raise UnexpectedTypeParameterCount(
                    position=parsed_arg.identifier.position,
                    expected_param_count=type.param_count,
                    found_param_count=len(parsed_type.params),
                )

            params = self._lookup_function_params(type_params, parsed_type)

        arg_type = VariableType(
            type=type,
            params=params,
            is_placeholder=arg_type_name in type_params,
            position=parsed_type.position,
            is_const=parsed_type.const,
        )

        return Argument(identifier=parsed_arg.identifier, type=arg_type)

    def _resolve_function_arguments(
        self, function: Function, type_params: Dict[str, Struct]
    ) -> List[Argument]:
        return [
            self._resolve_function_argument(type_params, parsed_arg)
            for parsed_arg in function.get_unresolved().parsed.get_arguments()
        ]

    def _lookup_function_param(
        self,
        type_params: Dict[str, Struct],
        param: parser.TypeLiteral | parser.FunctionPointerTypeLiteral,
    ) -> VariableType | FunctionPointer:
        if isinstance(param, parser.FunctionPointerTypeLiteral):
            return self._resolve_type(param)

        param_name = param.identifier.value
        if param_name in type_params:
            param_type: Struct | Enum = type_params[param_name]
            is_placeholder = True
        else:
            is_placeholder = False
            identifier = self._get_identifiable(param.identifier)

            if not isinstance(identifier, (Struct, Enum)):
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
        type_params: Dict[str, Struct],
        parsed_type: parser.TypeLiteral,
    ) -> List[VariableType | FunctionPointer]:
        looked_up_params: List[VariableType | FunctionPointer] = []

        for param in parsed_type.params:
            literal = param.literal

            looked_up_param = self._lookup_function_param(type_params, literal)
            looked_up_params.append(looked_up_param)

        return looked_up_params

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
        self, function: Function, type_params: Dict[str, Struct]
    ) -> List[VariableType | FunctionPointer] | Never:
        parsed_return_types = function.get_unresolved().parsed.get_return_types()

        if isinstance(parsed_return_types, parser.Never):
            return Never()

        return_types: List[VariableType | FunctionPointer] = []

        for parsed_return_type in parsed_return_types:
            if isinstance(parsed_return_type, parser.FunctionPointerTypeLiteral):
                return_types.append(self._resolve_type(parsed_return_type))
                continue

            return_type_name = parsed_return_type.identifier.value

            if return_type_name in type_params:
                type: Struct | Enum = type_params[return_type_name]
                params: List[VariableType | FunctionPointer] = []
            else:
                loaded_type = self._get_identifiable(parsed_return_type.identifier)

                if not isinstance(loaded_type, (Struct, Enum)):
                    raise InvalidReturnType(loaded_type)

                type = loaded_type

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
            if function.position.file != self.builtins_path:
                raise UnexpectedBuiltin(function.position)

            function.resolve(None)
            return

        resolver = FunctionBodyResolver(self, function, parsed_body)

        try:
            body = resolver.run()
        except CrossReferenceBaseException as e:
            self.exceptions.append(e)
            return

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
        else_body = branch.get_else_body()

        if else_body:
            resolved_else_body = self._resolve_function_body(else_body)
        else:
            resolved_else_body = None

        return Branch(
            condition=self._resolve_function_body(branch.condition),
            if_body=self._resolve_function_body(branch.get_if_body()),
            else_body=resolved_else_body,
            parsed=branch,
        )

    def _resolve_while_loop(self, while_loop: parser.WhileLoop) -> WhileLoop:
        return WhileLoop(
            condition=self._resolve_function_body(while_loop.condition),
            body=self._resolve_function_body(while_loop.body.value),
            parsed=while_loop,
        )

    def _resolve_call(
        self, call: parser.FunctionCall
    ) -> CallVariable | CallFunction | CallType | CallEnumConstructor:
        try:
            identifiable = self._get_identifiable_from_call(call)
        except UnknownIdentifier:
            return CallVariable(
                call.name(), bool(call.get_type_params()), call.position
            )

        type_params = [
            self._lookup_function_param(self.function.type_params, param)
            for param in call.get_type_params()
        ]

        if isinstance(identifiable, Function):
            return CallFunction(identifiable, type_params, call.position)

        if isinstance(identifiable, ImplicitFunctionImport):
            return CallFunction(identifiable.source, type_params, call.position)

        if isinstance(identifiable, EnumConstructor):
            var_type = VariableType(
                identifiable.enum, type_params, False, call.position, False
            )
            return CallEnumConstructor(identifiable, var_type, call.position)

        if isinstance(identifiable, ImplicitEnumConstructorImport):
            var_type = VariableType(
                identifiable.source.enum, type_params, False, call.position, False
            )
            return CallEnumConstructor(identifiable.source, var_type, call.position)

        if isinstance(identifiable, Import):
            raise NotImplementedError  # This should never happen

        else:
            var_type = VariableType(
                identifiable,
                [
                    self._lookup_function_param(self.function.type_params, param)
                    for param in call.get_type_params()
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

    def _resolve_struct_field_update(
        self, update: parser.StructFieldUpdate
    ) -> StructFieldUpdate:
        return StructFieldUpdate(
            parsed=update,
            new_value_expr=self._resolve_function_body(update.new_value_expr.value),
        )

    def _resolve_function_body_item(
        self, parsed_item: parser.FunctionBodyItem.types
    ) -> FunctionBodyItem:
        resolve_functions: Dict[
            Type[parser.FunctionBodyItem.types], Callable[..., FunctionBodyItem]
        ] = {
            parser.Assignment: self._resolve_assignment,
            parser.Boolean: BooleanLiteral,
            parser.Branch: self._resolve_branch,
            parser.Call: self._resolve_call_function_by_pointer,
            parser.Char: CharacterLiteral,
            parser.ForeachLoop: self._resolve_foreach_loop,
            parser.FunctionCall: self._resolve_call,
            parser.FunctionPointerTypeLiteral: self._resolve_function_pointer_literal,
            parser.GetFunctionPointer: self._resolve_get_function_pointer,
            parser.Integer: IntegerLiteral,
            parser.MatchBlock: self._resolve_match_block,
            parser.Return: self._resolve_return,
            parser.String: StringLiteral,
            parser.StructFieldQuery: StructFieldQuery,
            parser.StructFieldUpdate: self._resolve_struct_field_update,
            parser.UseBlock: self._resolve_use_block,
            parser.WhileLoop: self._resolve_while_loop,
        }

        assert set(resolve_functions.keys()) == set(parser.FunctionBodyItem.types.__args__)  # type: ignore
        return resolve_functions[type(parsed_item)](parsed_item)

    def _resolve_function_pointer_literal(
        self, parsed: parser.FunctionPointerTypeLiteral
    ) -> FunctionPointer:
        parsed_return_types = parsed.get_return_types()
        if isinstance(parsed_return_types, parser.Never):
            return_types: List[VariableType | FunctionPointer] | Never = Never()
        else:
            return_types = [
                self.cross_referencer._resolve_type(type)
                for type in parsed_return_types
            ]

        return FunctionPointer(
            parsed.position,
            argument_types=[
                self.cross_referencer._resolve_type(type)
                for type in parsed.get_arguments()
            ],
            return_types=return_types,
        )

    def _resolve_match_block(self, parsed: parser.MatchBlock) -> MatchBlock:
        blocks: List[CaseBlock | DefaultBlock] = []

        for block in parsed.blocks:
            if isinstance(block, parser.CaseBlock):
                blocks.append(self._resolve_case_block(block))
            else:
                blocks.append(self._resolve_default_block(block))

        return MatchBlock(parsed.position, blocks)

    def _resolve_case_block(self, parsed: parser.CaseBlock) -> CaseBlock:
        enum_type_name = parsed.label.enum_name.value
        variant_name = parsed.label.variant_name.value
        assert enum_type_name  # parser ensures this doesn't fail

        enum_type = self._get_identifiable_generic(enum_type_name, parsed.position)

        if not isinstance(enum_type, Enum):
            raise InvalidEnumType(parsed.position, enum_type)

        if variant_name not in enum_type.variants:
            raise InvalidEnumVariant(parsed.position, enum_type, variant_name)

        variables = [
            Variable(parsed_var, False) for parsed_var in parsed.label.get_variables()
        ]

        resolved_body = self._resolve_function_body(parsed.body.value)

        return CaseBlock(
            parsed.position,
            enum_type=enum_type,
            variant_name=variant_name,
            variables=variables,
            body=resolved_body,
        )

    def _resolve_default_block(self, parsed: parser.DefaultBlock) -> DefaultBlock:
        return DefaultBlock(
            parsed.position, self._resolve_function_body(parsed.body_block.value)
        )

    def _resolve_return(self, parsed: parser.Return) -> Return:
        return Return(parsed)

    def _resolve_call_function_by_pointer(
        self, call: parser.Call
    ) -> CallFunctionByPointer:
        return CallFunctionByPointer(call.position)

    def _resolve_get_function_pointer(
        self, parsed: parser.GetFunctionPointer
    ) -> GetFunctionPointer:
        builtins_key = (self.cross_referencer.builtins_path, parsed.function_name.value)
        key = (parsed.position.file, parsed.function_name.value)

        if builtins_key in self.cross_referencer.identifiers:
            target = self.cross_referencer.identifiers[builtins_key]
        elif key in self.cross_referencer.identifiers:
            target = self.cross_referencer.identifiers[key]
        else:
            raise FunctionPointerTargetNotFound(
                parsed.position, parsed.function_name.value
            )

        if isinstance(target, Import):
            target = target.resolved().source

        if isinstance(target, (Function, EnumConstructor)):
            return GetFunctionPointer(parsed.position, target)

        if isinstance(target, (ImplicitFunctionImport, ImplicitEnumConstructorImport)):
            return GetFunctionPointer(parsed.position, target.source)

        raise InvalidFunctionPointerTarget(parsed.position, target)

    def _resolve_assignment(self, parsed: parser.Assignment) -> Assignment:
        variables = [Variable(var, False) for var in parsed.variables.value]
        body = self._resolve_function_body(parsed.body_block.value)
        return Assignment(parsed, variables, body)

    def _resolve_use_block(self, parsed: parser.UseBlock) -> UseBlock:
        variables = [
            Variable(parsed_var, False) for parsed_var in parsed.variables.value
        ]
        body = self._resolve_function_body(parsed.body_block.value)
        return UseBlock(parsed, variables, body)

    def _resolve_foreach_loop(self, parsed: parser.ForeachLoop) -> ForeachLoop:
        body = self._resolve_function_body(parsed.body.value)
        return ForeachLoop(parsed, body)

    def _get_identifiable_from_call(self, call: parser.FunctionCall) -> Identifiable:
        return self._get_identifiable_generic(call.name(), call.position)

    def _get_identifiable_generic(self, name: str, position: Position) -> Identifiable:
        return self.cross_referencer._get_identifiable_generic(name, position)

    def _lookup_function_param(
        self,
        type_params: Dict[str, Struct],
        param: parser.TypeLiteral | parser.FunctionPointerTypeLiteral,
    ) -> VariableType | FunctionPointer:
        return self.cross_referencer._lookup_function_param(type_params, param)

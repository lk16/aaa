from __future__ import annotations

from pathlib import Path
from typing import Any

from basil.models import Position

from aaa import AaaModel
from aaa.parser import models as parser


class AaaCrossReferenceModel(AaaModel):
    def __init__(self, position: Position) -> None:
        self.position = position


class EnumConstructor(AaaCrossReferenceModel):
    def __init__(self, enum: Enum, variant_name: str) -> None:
        position = Position(enum.position.file, -1, -1)
        self.enum = enum
        self.variant_name = variant_name
        self.name = f"{enum.name}:{variant_name}"
        super().__init__(position)

    def identify(self) -> tuple[Path, str]:
        return (self.position.file, self.name)


class Function(AaaCrossReferenceModel):
    class Unresolved:
        def __init__(self, parsed: parser.Function) -> None:
            self.parsed = parsed

            self.type_params = {param.value: param for param in parsed.get_params()}

    class WithSignature:
        def __init__(
            self,
            parsed_body: parser.FunctionBody | None,
            type_params: dict[str, Struct],
            arguments: list[Argument],
            return_types: list[VariableType | FunctionPointer] | Never,
        ) -> None:
            self.parsed_body = parsed_body
            self.type_params = type_params
            self.arguments = arguments
            self.return_types = return_types

    class Resolved:
        def __init__(
            self,
            type_params: dict[str, Struct],
            arguments: list[Argument],
            return_types: list[VariableType | FunctionPointer] | Never,
            body: FunctionBody | None,
        ) -> None:
            self.type_params = type_params
            self.arguments = arguments
            self.return_types = return_types
            self.body = body

    def __init__(self, parsed: parser.Function) -> None:
        self.state: Function.Resolved | Function.Unresolved | Function.WithSignature = (
            Function.Unresolved(parsed)
        )
        self.end_position = parsed.get_end_position()
        self.func_name = parsed.get_func_name()
        self.struct_name = parsed.get_type_name()
        self.name = parsed.get_name()

        super().__init__(parsed.position)

    def get_unresolved(self) -> Function.Unresolved:
        assert isinstance(self.state, Function.Unresolved)
        return self.state

    def get_with_signature(self) -> Function.WithSignature:
        assert isinstance(self.state, Function.WithSignature)
        return self.state

    def is_member_function(self) -> bool:
        return self.struct_name != ""

    def is_test(self) -> bool:
        return (
            not self.is_member_function()
            and self.func_name.startswith("test_")
            and self.position.file.name.startswith("test_")
        )

    @property
    def arguments(self) -> list[Argument]:
        assert isinstance(self.state, Function.WithSignature | Function.Resolved)
        return self.state.arguments

    @property
    def return_types(self) -> list[VariableType | FunctionPointer] | Never:
        assert isinstance(self.state, Function.WithSignature | Function.Resolved)
        return self.state.return_types

    @property
    def type_params(self) -> dict[str, Struct]:
        assert isinstance(self.state, Function.WithSignature | Function.Resolved)
        return self.state.type_params

    @property
    def type_param_names(self) -> list[str]:
        type_params = sorted(self.type_params.values(), key=lambda t: t.position)
        return [struct.name for struct in type_params]

    @property
    def body(self) -> FunctionBody:
        assert isinstance(self.state, Function.Resolved)
        assert self.state.body
        return self.state.body

    def add_signature(
        self,
        parsed_body: parser.FunctionBody | None,
        type_params: dict[str, Struct],
        arguments: list[Argument],
        return_types: list[VariableType | FunctionPointer] | Never,
    ) -> None:
        assert isinstance(self.state, Function.Unresolved)
        self.state = Function.WithSignature(
            parsed_body, type_params, arguments, return_types
        )

    def is_resolved(self) -> bool:
        return isinstance(self.state, Function.Resolved)

    def resolve(self, body: FunctionBody | None) -> None:
        assert isinstance(self.state, Function.WithSignature)
        self.state = Function.Resolved(
            self.state.type_params,
            self.state.arguments,
            self.state.return_types,
            body,
        )

    def identify(self) -> tuple[Path, str]:
        return (self.position.file, self.name)


class Argument(AaaCrossReferenceModel):
    def __init__(
        self,
        type: VariableType | FunctionPointer,
        identifier: parser.Identifier,
    ) -> None:
        self.type = type
        self.name = identifier.value
        super().__init__(identifier.position)


class FunctionBody(AaaCrossReferenceModel):
    def __init__(
        self, parsed: parser.FunctionBody, items: list[FunctionBodyItem]
    ) -> None:
        self.items = items
        super().__init__(parsed.position)


class Import(AaaCrossReferenceModel):
    class Unresolved:
        ...

    class Resolved:
        def __init__(self, source: Identifiable) -> None:
            self.source = source

    def __init__(self, import_item: parser.ImportItem, import_: parser.Import) -> None:
        self.state: Import.Resolved | Import.Unresolved = Import.Unresolved()
        self.source_file = import_.get_source_file()
        self.source_name = import_item.original.value
        self.name = import_item.imported.value
        super().__init__(import_item.position)

    @property
    def source(self) -> Identifiable:
        assert isinstance(self.state, Import.Resolved)
        return self.state.source

    def resolve(self, source: Identifiable) -> None:
        assert isinstance(self.state, Import.Unresolved)
        self.state = Import.Resolved(source)

    def is_resolved(self) -> bool:
        return isinstance(self.state, Import.Resolved)

    def resolved(self) -> Import.Resolved:
        assert isinstance(self.state, Import.Resolved)
        return self.state

    def identify(self) -> tuple[Path, str]:
        return (self.position.file, self.name)


class ImplicitFunctionImport(AaaCrossReferenceModel):
    def __init__(self, source: Function) -> None:
        self.source = source
        self.name = self.source.name

    def identify(self) -> tuple[Path, str]:
        return (self.position.file, self.name)


class ImplicitEnumConstructorImport(AaaCrossReferenceModel):
    def __init__(self, source: EnumConstructor) -> None:
        self.source = source
        self.name = self.source.name

    def identify(self) -> tuple[Path, str]:
        return (self.position.file, self.name)


class Struct(AaaCrossReferenceModel):
    class Unresolved:
        def __init__(
            self,
            parsed_field_types: dict[
                str,
                parser.TypeLiteral | parser.FunctionPointerTypeLiteral,
            ],
            parsed_params: list[parser.Identifier],
        ) -> None:
            self.parsed_field_types = parsed_field_types
            self.parsed_params = parsed_params

    class Resolved:
        def __init__(
            self,
            type_params: dict[str, Struct],
            fields: dict[str, VariableType | FunctionPointer],
        ) -> None:
            self.type_params = type_params
            self.fields = fields

    @classmethod
    def from_parsed_struct(
        cls,
        struct: parser.Struct,
        fields: dict[str, parser.TypeLiteral | parser.FunctionPointerTypeLiteral],
    ) -> Struct:
        return Struct(struct.position, struct.get_name(), struct.get_params(), fields)

    @classmethod
    def from_identifier(cls, identifier: parser.Identifier) -> Struct:
        return Struct(identifier.position, identifier.value, [], {})

    def __init__(
        self,
        position: Position,
        name: str,
        params: list[parser.Identifier],
        fields: dict[
            str,
            parser.TypeLiteral | parser.FunctionPointerTypeLiteral,
        ],
    ) -> None:
        self.state: Struct.Resolved | Struct.Unresolved = Struct.Unresolved(
            fields, params
        )
        self.param_count = len(params)
        self.name = name
        super().__init__(position)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Struct):
            raise TypeError

        return self.name == other.name and self.position.file == other.position.file

    @property
    def fields(self) -> dict[str, VariableType | FunctionPointer]:
        assert isinstance(self.state, Struct.Resolved)
        return self.state.fields

    @property
    def type_params(self) -> dict[str, Struct]:
        assert isinstance(self.state, Struct.Resolved)
        return self.state.type_params

    def param_dict(
        self, var_type: VariableType
    ) -> dict[str, VariableType | FunctionPointer]:
        struct_type_placeholders = [
            struct.name
            for struct in sorted(self.type_params.values(), key=lambda s: s.position)
        ]

        return dict(zip(struct_type_placeholders, var_type.params, strict=True))

    def get_unresolved(self) -> Struct.Unresolved:
        assert isinstance(self.state, Struct.Unresolved)
        return self.state

    def resolve(
        self,
        type_params: dict[str, Struct],
        fields: dict[str, VariableType | FunctionPointer],
    ) -> None:
        assert isinstance(self.state, Struct.Unresolved)
        self.state = Struct.Resolved(type_params, fields)

    def is_resolved(self) -> bool:
        return isinstance(self.state, Struct.Resolved)

    def identify(self) -> tuple[Path, str]:
        return (self.position.file, self.name)


class Enum(AaaCrossReferenceModel):
    class Unresolved:
        def __init__(
            self,
            variants: list[parser.EnumVariant],
            parsed_params: list[parser.Identifier],
        ) -> None:
            self.parsed_variants = {
                variant.name.value: variant.get_data() for variant in variants
            }

            self.parsed_params = parsed_params

            # This can't fail, an enum needs to have at least one variant
            self.zero_variant = variants[0].name.value

    class Resolved:
        def __init__(
            self,
            type_params: dict[str, Struct],
            variants: dict[str, list[VariableType | FunctionPointer]],
            zero_variant: str,
        ) -> None:
            self.type_params = type_params

            if variants and zero_variant not in variants:
                raise ValueError("zero value not in variants")

            self.variants = variants
            self.zero_variant = zero_variant

    def __init__(
        self,
        position: Position,
        name: str,
        params: list[parser.Identifier],
        variants: list[parser.EnumVariant],
    ) -> None:
        self.state: Enum.Resolved | Enum.Unresolved = Enum.Unresolved(variants, params)
        self.param_count = len(params)
        self.name = name
        super().__init__(position)

    @classmethod
    def from_parsed_enum(cls, enum: parser.Enum) -> Enum:
        return Enum(
            enum.position, enum.get_name(), enum.get_params(), enum.get_variants()
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Enum):
            raise TypeError

        return self.name == other.name and self.position == other.position

    @property
    def variants(self) -> dict[str, list[VariableType | FunctionPointer]]:
        assert isinstance(self.state, Enum.Resolved)
        return self.state.variants

    @property
    def zero_variant(self) -> str:
        return self.state.zero_variant

    def get_unresolved(self) -> Enum.Unresolved:
        assert isinstance(self.state, Enum.Unresolved)
        return self.state

    def get_resolved(self) -> Enum.Resolved:
        assert isinstance(self.state, Enum.Resolved)
        return self.state

    def resolve(
        self,
        type_params: dict[str, Struct],
        variants: dict[str, list[VariableType | FunctionPointer]],
    ) -> None:
        assert isinstance(self.state, Enum.Unresolved)
        self.state = Enum.Resolved(type_params, variants, self.state.zero_variant)

    def param_dict(
        self, var_type: VariableType
    ) -> dict[str, VariableType | FunctionPointer]:
        struct_type_placeholders = [
            enum.name
            for enum in sorted(
                self.get_resolved().type_params.values(), key=lambda s: s.position
            )
        ]

        return dict(zip(struct_type_placeholders, var_type.params, strict=True))

    def is_resolved(self) -> bool:
        return isinstance(self.state, Enum.Resolved)

    def identify(self) -> tuple[Path, str]:
        return (self.position.file, self.name)


class VariableType(AaaCrossReferenceModel):
    def __init__(
        self,
        type: Struct | Enum,
        params: list[VariableType | FunctionPointer],
        is_placeholder: bool,
        position: Position,
        is_const: bool,
    ) -> None:
        self.type = type
        self.params = params
        self.is_placeholder = is_placeholder
        self.name = self.type.name
        self.is_const = is_const
        super().__init__(position)

    def __repr__(self) -> str:  # pragma: nocover
        output = self.name

        if self.params:
            output += "["
            output += ", ".join(repr(param) for param in self.params)
            output += "]"

        if self.is_const:
            return f"(const {output})"

        return output

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, VariableType):  # pragma: nocover
            raise TypeError

        return (
            self.type == other.type
            and self.params == other.params
            and self.is_const == other.is_const
        )


class FunctionPointer(AaaCrossReferenceModel):
    def __init__(
        self,
        position: Position,
        argument_types: list[VariableType | FunctionPointer],
        return_types: list[VariableType | FunctionPointer] | Never,
    ) -> None:
        self.argument_types = argument_types
        self.return_types = return_types
        super().__init__(position)

    def __repr__(self) -> str:
        args = ", ".join(repr(arg) for arg in self.argument_types)

        if isinstance(self.return_types, Never):
            returns = "never"
        else:
            returns = ", ".join(repr(return_) for return_ in self.return_types)

        return f"fn[{args}][{returns}]"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, FunctionPointer):
            raise TypeError

        return (
            self.argument_types == other.argument_types
            and self.return_types == other.return_types
        )


class Never:
    """
    Indicator that a FunctionBodyItem never returns.
    Examples for which this is useful: return, continue, break, exit
    """

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Never):
            raise TypeError

        return True


class IntegerLiteral(AaaCrossReferenceModel):
    def __init__(self, parsed: parser.Integer) -> None:
        self.value = parsed.value
        super().__init__(parsed.position)


class StringLiteral(AaaCrossReferenceModel):
    def __init__(self, parsed: parser.String) -> None:
        self.value = parsed.value
        super().__init__(parsed.position)


class CharacterLiteral(AaaCrossReferenceModel):
    def __init__(self, parsed: parser.Char) -> None:
        self.value = parsed.value
        super().__init__(parsed.position)


class BooleanLiteral(AaaCrossReferenceModel):
    def __init__(self, parsed: parser.Boolean) -> None:
        self.value = parsed.value
        super().__init__(parsed.position)


class WhileLoop(AaaCrossReferenceModel):
    def __init__(
        self,
        condition: FunctionBody,
        body: FunctionBody,
        parsed: parser.WhileLoop,
    ) -> None:
        self.condition = condition
        self.body = body
        super().__init__(parsed.position)


class CallVariable(AaaCrossReferenceModel):
    def __init__(self, name: str, has_type_params: bool, position: Position) -> None:
        self.has_type_params = has_type_params
        self.name = name
        super().__init__(position)


class CallFunction(AaaCrossReferenceModel):
    def __init__(
        self,
        function: Function,
        type_params: list[VariableType | FunctionPointer],
        position: Position,
    ) -> None:
        self.function = function
        self.type_params = type_params
        super().__init__(position)


class CallEnumConstructor(AaaCrossReferenceModel):
    def __init__(
        self,
        enum_ctor: EnumConstructor,
        enum_var_type: VariableType,
        position: Position,
    ) -> None:
        self.enum_var_type = enum_var_type
        self.enum_ctor = enum_ctor
        super().__init__(position)


class CallType(AaaCrossReferenceModel):
    def __init__(self, var_type: VariableType) -> None:
        self.var_type = var_type
        super().__init__(var_type.position)


class Branch(AaaCrossReferenceModel):
    def __init__(
        self,
        condition: FunctionBody,
        if_body: FunctionBody,
        else_body: FunctionBody | None,
        parsed: parser.Branch,
    ) -> None:
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body
        super().__init__(parsed.position)


class StructFieldQuery(AaaCrossReferenceModel):
    def __init__(self, parsed: parser.StructFieldQuery) -> None:
        self.field_name = parsed.field_name
        self.operator_position = parsed.operator_position
        super().__init__(parsed.position)


class StructFieldUpdate(AaaCrossReferenceModel):
    def __init__(
        self, parsed: parser.StructFieldUpdate, new_value_expr: FunctionBody
    ) -> None:
        self.field_name = parsed.field_name
        self.new_value_expr = new_value_expr
        self.operator_position = parsed.operator_position
        super().__init__(parsed.position)


class ForeachLoop(AaaCrossReferenceModel):
    def __init__(self, parsed: parser.ForeachLoop, body: FunctionBody) -> None:
        self.body = body
        super().__init__(parsed.position)


class Variable(AaaCrossReferenceModel):
    def __init__(self, parsed: parser.Identifier, is_func_arg: bool) -> None:
        self.name = parsed.value
        self.is_func_arg = is_func_arg
        super().__init__(parsed.position)


class Assignment(AaaCrossReferenceModel):
    def __init__(
        self,
        parsed: parser.Assignment,
        variables: list[Variable],
        body: FunctionBody,
    ) -> None:
        self.variables = variables
        self.body = body
        super().__init__(parsed.position)


class UseBlock(AaaCrossReferenceModel):
    def __init__(
        self,
        parsed: parser.UseBlock,
        variables: list[Variable],
        body: FunctionBody,
    ) -> None:
        self.variables = variables
        self.body = body
        super().__init__(parsed.position)


class MatchBlock(AaaCrossReferenceModel):
    def __init__(
        self, position: Position, blocks: list[CaseBlock | DefaultBlock]
    ) -> None:
        self.blocks = blocks
        super().__init__(position)


class CaseBlock(AaaCrossReferenceModel):  # NOTE: This is NOT a FunctionBodyItem
    def __init__(
        self,
        position: Position,
        enum_type: Enum,
        variant_name: str,
        variables: list[Variable],
        body: FunctionBody,
    ) -> None:
        self.enum_type = enum_type
        self.variant_name = variant_name
        self.variables = variables
        self.body = body
        super().__init__(position)


class DefaultBlock(AaaCrossReferenceModel):  # NOTE: This is NOT a FunctionBodyItem
    def __init__(self, position: Position, body: FunctionBody) -> None:
        self.body = body
        super().__init__(position)


class Return(AaaCrossReferenceModel):
    def __init__(self, parsed: parser.Return) -> None:
        super().__init__(parsed.position)


class GetFunctionPointer(AaaCrossReferenceModel):
    def __init__(self, position: Position, target: Function | EnumConstructor) -> None:
        self.target = target
        super().__init__(position)


class CallFunctionByPointer(AaaCrossReferenceModel):
    ...


Identifiable = (
    EnumConstructor
    | Enum
    | Function
    | ImplicitEnumConstructorImport
    | ImplicitFunctionImport
    | Import
    | Struct
)


FunctionBodyItem = (
    Assignment
    | BooleanLiteral
    | Branch
    | CallEnumConstructor
    | CallFunction
    | CallFunctionByPointer
    | CallType
    | CallVariable
    | CharacterLiteral
    | ForeachLoop
    | FunctionPointer
    | GetFunctionPointer
    | IntegerLiteral
    | MatchBlock
    | Return
    | StringLiteral
    | StructFieldQuery
    | StructFieldUpdate
    | UseBlock
    | WhileLoop
)

IdentifiablesDict = dict[tuple[Path, str], Identifiable]


class CrossReferencerOutput(AaaModel):
    def __init__(
        self,
        structs: dict[tuple[Path, str], Struct],
        enums: dict[tuple[Path, str], Enum],
        functions: dict[tuple[Path, str], Function],
        imports: dict[tuple[Path, str], Import],
        builtins_path: Path,
        entrypoint: Path,
    ) -> None:
        for struct in structs.values():
            assert struct.is_resolved()

        for enum in enums.values():
            assert enum.is_resolved()

        for function in functions.values():
            assert function.is_resolved()

        for import_ in imports.values():
            assert import_.is_resolved()

        self.structs = structs
        self.enums = enums
        self.functions = functions
        self.imports = imports
        self.builtins_path = builtins_path
        self.entrypoint = entrypoint

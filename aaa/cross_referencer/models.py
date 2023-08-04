from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from aaa import AaaModel, Position
from aaa.parser import models as parser


class AaaCrossReferenceModel(AaaModel):
    def __init__(self, position: Position) -> None:
        self.position = position


class Identifiable(AaaCrossReferenceModel):
    def __init__(self, position: Position, name: str) -> None:
        self.name = name
        super().__init__(position)

    def identify(self) -> Tuple[Path, str]:
        return (self.position.file, self.name)


IdentifiablesDict = Dict[Tuple[Path, str], Identifiable]


class EnumConstructor(Identifiable):
    def __init__(self, enum: Enum, variant_name: str) -> None:
        position = Position(enum.position.file, -1, -1)
        self.enum = enum
        self.variant_name = variant_name
        name = f"{enum.name}:{variant_name}"
        super().__init__(position, name)


class Function(Identifiable):
    class Unresolved:
        def __init__(self, parsed: parser.Function) -> None:
            self.parsed = parsed

    class WithSignature:
        def __init__(
            self,
            parsed_body: Optional[parser.FunctionBody],
            type_params: Dict[str, Struct],
            arguments: List[Argument],
            return_types: List[VariableType | FunctionPointer] | Never,
        ) -> None:
            self.parsed_body = parsed_body
            self.type_params = type_params
            self.arguments = arguments
            self.return_types = return_types

    class Resolved:
        def __init__(
            self,
            type_params: Dict[str, Struct],
            arguments: List[Argument],
            return_types: List[VariableType | FunctionPointer] | Never,
            body: Optional[FunctionBody],
        ) -> None:
            self.type_params = type_params
            self.arguments = arguments
            self.return_types = return_types
            self.body: Optional[FunctionBody] = None
            self.body = body

    def __init__(self, parsed: parser.Function) -> None:
        self.state: Function.Resolved | Function.Unresolved | Function.WithSignature = (
            Function.Unresolved(parsed)
        )
        self.end_position = parsed.end_position

        self.func_name = parsed.func_name.name

        if parsed.struct_name:
            self.struct_name = parsed.struct_name.name
        else:
            self.struct_name = ""

        if parsed.struct_name:
            name = f"{self.struct_name}:{self.func_name}"
        else:
            name = self.func_name

        super().__init__(parsed.position, name)

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
    def arguments(self) -> List[Argument]:
        assert isinstance(self.state, (Function.WithSignature, Function.Resolved))
        return self.state.arguments

    @property
    def return_types(self) -> List[VariableType | FunctionPointer] | Never:
        assert isinstance(self.state, (Function.WithSignature, Function.Resolved))
        return self.state.return_types

    @property
    def type_params(self) -> Dict[str, Struct]:
        assert isinstance(self.state, (Function.WithSignature, Function.Resolved))
        return self.state.type_params

    @property
    def body(self) -> FunctionBody:
        assert isinstance(self.state, Function.Resolved)
        assert self.state.body
        return self.state.body

    def add_signature(
        self,
        parsed_body: Optional[parser.FunctionBody],
        type_params: Dict[str, Struct],
        arguments: List[Argument],
        return_types: List[VariableType | FunctionPointer] | Never,
    ) -> None:
        assert isinstance(self.state, Function.Unresolved)
        self.state = Function.WithSignature(
            parsed_body, type_params, arguments, return_types
        )

    def is_resolved(self) -> bool:
        return isinstance(self.state, Function.Resolved)

    def resolve(self, body: Optional[FunctionBody]) -> None:
        assert isinstance(self.state, Function.WithSignature)
        self.state = Function.Resolved(
            self.state.type_params,
            self.state.arguments,
            self.state.return_types,
            body,
        )


class Argument(AaaCrossReferenceModel):
    def __init__(
        self, type: VariableType | FunctionPointer, identifier: parser.Identifier
    ) -> None:
        self.type = type
        self.name = identifier.name
        super().__init__(identifier.position)


class FunctionBodyItem(AaaCrossReferenceModel):
    ...


class FunctionBody(FunctionBodyItem):
    def __init__(
        self, parsed: parser.FunctionBody, items: List[FunctionBodyItem]
    ) -> None:
        self.items = items
        super().__init__(parsed.position)


class Import(Identifiable):
    class Unresolved:
        ...

    class Resolved:
        def __init__(self, source: Identifiable) -> None:
            self.source = source

    def __init__(self, import_item: parser.ImportItem, import_: parser.Import) -> None:
        self.state: Import.Resolved | Import.Unresolved = Import.Unresolved()
        self.source_file = import_.source_file
        self.source_name = import_item.original.name
        super().__init__(import_item.position, import_item.imported.name)

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


class ImplicitFunctionImport(Identifiable):
    def __init__(self, source: Function) -> None:
        self.source = source


class ImplicitEnumConstructorImport(Identifiable):
    def __init__(self, source: EnumConstructor) -> None:
        self.source = source


class Struct(Identifiable):
    class Unresolved:
        def __init__(self, parsed: parser.TypeLiteral | parser.Struct) -> None:
            self.parsed_field_types: Dict[str, parser.TypeLiteral] = {}

            if isinstance(parsed, parser.Struct):
                self.parsed_field_types = parsed.fields

    class Resolved:
        def __init__(self, fields: Dict[str, VariableType]) -> None:
            self.fields = fields

    def __init__(
        self,
        parsed: parser.TypeLiteral | parser.Struct,
        param_count: int,
    ) -> None:
        self.state: Struct.Resolved | Struct.Unresolved = Struct.Unresolved(parsed)
        self.param_count = param_count
        super().__init__(parsed.position, parsed.identifier.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Struct):
            return False

        return self.name == other.name and self.position == other.position

    @property
    def fields(self) -> Dict[str, VariableType]:
        assert isinstance(self.state, Struct.Resolved)
        return self.state.fields

    def get_unresolved(self) -> Struct.Unresolved:
        assert isinstance(self.state, Struct.Unresolved)
        return self.state

    def resolve(
        self,
        fields: Dict[str, VariableType],
    ) -> None:
        assert isinstance(self.state, Struct.Unresolved)
        self.state = Struct.Resolved(fields)

    def is_resolved(self) -> bool:
        return isinstance(self.state, Struct.Resolved)


class Enum(Identifiable):
    class Unresolved:
        def __init__(self, parsed: parser.Enum) -> None:
            self.parsed_variants: Dict[str, List[parser.TypeLiteral]] = {}

            for variant in parsed.variants:
                self.parsed_variants[variant.name.name] = variant.associated_data

            # This can't fail, an enum needs to have at least one variant
            self.zero_variant = parsed.variants[0].name.name

    class Resolved:
        def __init__(
            self,
            variants: Dict[str, List[VariableType | FunctionPointer]],
            zero_variant: str,
        ) -> None:
            if variants and zero_variant not in variants:
                raise ValueError("zero value not in variants")

            self.variants = variants
            self.zero_variant = zero_variant

    def __init__(self, parsed: parser.Enum, param_count: int) -> None:
        self.state: Enum.Resolved | Enum.Unresolved = Enum.Unresolved(parsed)
        self.param_count = param_count
        super().__init__(parsed.position, parsed.identifier.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Enum):
            return False

        return self.name == other.name and self.position == other.position

    @property
    def variants(self) -> Dict[str, List[VariableType | FunctionPointer]]:
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
        self, variants: Dict[str, List[VariableType | FunctionPointer]]
    ) -> None:
        assert isinstance(self.state, Enum.Unresolved)
        self.state = Enum.Resolved(variants, self.state.zero_variant)

    def is_resolved(self) -> bool:
        return isinstance(self.state, Enum.Resolved)


class VariableType(AaaCrossReferenceModel):
    def __init__(
        self,
        type: Struct | Enum,
        params: List[VariableType],
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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VariableType):  # pragma: nocover
            return False

        return (
            self.type == other.type
            and self.params == other.params
            and self.is_const == other.is_const
        )


class FunctionPointer(AaaCrossReferenceModel):
    def __init__(
        self,
        position: Position,
        argument_types: List[VariableType | FunctionPointer],
        return_types: List[VariableType | FunctionPointer] | Never,
    ) -> None:
        self.argument_types = argument_types
        self.return_types = return_types
        super().__init__(position)

    def __repr__(self) -> str:
        # TODO test
        args = ", ".join(repr(arg) for arg in self.argument_types)

        if isinstance(self.return_types, Never):
            returns = "never"
        else:
            returns = ", ".join(repr(return_) for return_ in self.return_types)

        return f"fn[{args}][{returns}]"

    def __eq__(self, other: Any) -> bool:
        return (
            type(other) == type(self)
            and self.argument_types == other.argument_types
            and self.return_types == other.return_types
        )


class Never:
    """
    Indicator that a FunctionBodyItem never returns.
    Examples for which this is useful: return, continue, break, exit
    """

    ...


class IntegerLiteral(FunctionBodyItem):
    def __init__(self, parsed: parser.IntegerLiteral) -> None:
        self.value = parsed.value
        super().__init__(parsed.position)


class StringLiteral(FunctionBodyItem, parser.StringLiteral):
    def __init__(self, parsed: parser.StringLiteral) -> None:
        self.value = parsed.value
        super().__init__(parsed.position)


class BooleanLiteral(FunctionBodyItem, parser.BooleanLiteral):
    def __init__(self, parsed: parser.BooleanLiteral) -> None:
        self.value = parsed.value
        super().__init__(parsed.position)


class WhileLoop(FunctionBodyItem):
    def __init__(
        self,
        condition: FunctionBody,
        body: FunctionBody,
        parsed: parser.WhileLoop,
    ) -> None:
        self.condition = condition
        self.body = body
        super().__init__(parsed.position)


class CallVariable(FunctionBodyItem):
    def __init__(self, name: str, has_type_params: bool, position: Position) -> None:
        self.has_type_params = has_type_params
        self.name = name
        super().__init__(position)


class CallFunction(FunctionBodyItem):
    def __init__(
        self, function: Function, type_params: List[VariableType], position: Position
    ) -> None:
        self.function = function
        self.type_params = type_params
        super().__init__(position)


class CallEnumConstructor(FunctionBodyItem):
    def __init__(
        self,
        enum_ctor: EnumConstructor,
        enum_var_type: VariableType,
        position: Position,
    ) -> None:
        self.enum_var_type = enum_var_type
        self.enum_ctor = enum_ctor
        super().__init__(position)


class CallType(FunctionBodyItem):
    def __init__(self, var_type: VariableType) -> None:
        self.var_type = var_type
        super().__init__(var_type.position)


class Branch(FunctionBodyItem):
    def __init__(
        self,
        condition: FunctionBody,
        if_body: FunctionBody,
        else_body: Optional[FunctionBody],
        parsed: parser.Branch,
    ) -> None:
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body
        super().__init__(parsed.position)


class StructFieldQuery(FunctionBodyItem):
    def __init__(self, parsed: parser.StructFieldQuery) -> None:
        self.field_name = parsed.field_name
        self.operator_position = parsed.operator_position
        super().__init__(parsed.position)


class StructFieldUpdate(FunctionBodyItem):
    def __init__(
        self, parsed: parser.StructFieldUpdate, new_value_expr: FunctionBody
    ) -> None:
        self.field_name = parsed.field_name
        self.new_value_expr = new_value_expr
        self.operator_position = parsed.operator_position
        super().__init__(parsed.position)


class ForeachLoop(FunctionBodyItem):
    def __init__(self, parsed: parser.ForeachLoop, body: FunctionBody) -> None:
        self.body = body
        super().__init__(parsed.position)


class Variable(FunctionBodyItem):
    def __init__(self, parsed: parser.Identifier, is_func_arg: bool) -> None:
        self.name = parsed.name
        self.is_func_arg = is_func_arg
        super().__init__(parsed.position)


class Assignment(FunctionBodyItem):
    def __init__(
        self, parsed: parser.Assignment, variables: List[Variable], body: FunctionBody
    ) -> None:
        self.variables = variables
        self.body = body
        super().__init__(parsed.position)


class UseBlock(FunctionBodyItem):
    def __init__(
        self, parsed: parser.UseBlock, variables: List[Variable], body: FunctionBody
    ) -> None:
        self.variables = variables
        self.body = body
        super().__init__(parsed.position)


class MatchBlock(FunctionBodyItem):
    def __init__(
        self, position: Position, blocks: List[CaseBlock | DefaultBlock]
    ) -> None:
        self.blocks = blocks
        super().__init__(position)


class CaseBlock(AaaCrossReferenceModel):  # NOTE: This is NOT a FunctionBodyItem
    def __init__(
        self,
        position: Position,
        enum_type: Enum,
        variant_name: str,
        variables: List[Variable],
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


class Return(FunctionBodyItem):
    def __init__(self, parsed: parser.Return) -> None:
        super().__init__(parsed.position)


class GetFunctionPointer(FunctionBodyItem):
    def __init__(self, position: Position, target: Function) -> None:
        self.target = target
        super().__init__(position)


class CallFunctionByPointer(FunctionBodyItem):
    ...


class CrossReferencerOutput(AaaModel):
    def __init__(
        self,
        structs: Dict[Tuple[Path, str], Struct],
        enums: Dict[Tuple[Path, str], Enum],
        functions: Dict[Tuple[Path, str], Function],
        imports: Dict[Tuple[Path, str], Import],
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

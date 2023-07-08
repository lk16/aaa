from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

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


class Function(Identifiable):
    class Unresolved:
        def __init__(self, parsed: parser.Function) -> None:
            self.parsed = parsed

    class WithSignature:
        def __init__(
            self,
            parsed_body: Optional[parser.FunctionBody],
            type_params: Dict[str, Type],
            arguments: List[Argument],
            return_types: List[VariableType] | Never,
            is_enum_ctor: bool,
        ) -> None:
            self.parsed_body = parsed_body
            self.type_params = type_params
            self.arguments = arguments
            self.return_types = return_types
            self.is_enum_ctor = is_enum_ctor

    class Resolved:
        def __init__(
            self,
            type_params: Dict[str, Type],
            arguments: List[Argument],
            return_types: List[VariableType] | Never,
            is_enum_ctor: bool,
            body: Optional[FunctionBody],
        ) -> None:
            self.type_params = type_params
            self.arguments = arguments
            self.return_types = return_types
            self.body: Optional[FunctionBody] = None
            self.is_enum_ctor = is_enum_ctor
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
    def return_types(self) -> List[VariableType] | Never:
        assert isinstance(self.state, (Function.WithSignature, Function.Resolved))
        return self.state.return_types

    @property
    def type_params(self) -> Dict[str, Type]:
        assert isinstance(self.state, (Function.WithSignature, Function.Resolved))
        return self.state.type_params

    @property
    def body(self) -> FunctionBody:
        assert isinstance(self.state, Function.Resolved)
        assert self.state.body
        return self.state.body

    @property
    def is_enum_ctor(self) -> bool:
        assert isinstance(self.state, (Function.WithSignature, Function.Resolved))
        return self.state.is_enum_ctor

    def add_signature(
        self,
        parsed_body: Optional[parser.FunctionBody],
        type_params: Dict[str, Type],
        arguments: List[Argument],
        return_types: List[VariableType] | Never,
        is_enum_ctor: bool,
    ) -> None:
        assert isinstance(self.state, Function.Unresolved)
        self.state = Function.WithSignature(
            parsed_body, type_params, arguments, return_types, is_enum_ctor
        )

    def is_resolved(self) -> bool:
        return isinstance(self.state, Function.Resolved)

    def resolve(self, body: Optional[FunctionBody]) -> None:
        assert isinstance(self.state, Function.WithSignature)
        self.state = Function.Resolved(
            self.state.type_params,
            self.state.arguments,
            self.state.return_types,
            self.state.is_enum_ctor,
            body,
        )


class Argument(AaaCrossReferenceModel):
    def __init__(self, var_type: VariableType, identifier: parser.Identifier) -> None:
        self.var_type = var_type
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


class Type(Identifiable):
    class Unresolved:
        def __init__(
            self, parsed: parser.TypeLiteral | parser.Struct | parser.Enum
        ) -> None:
            self.parsed_field_types: Dict[str, parser.TypeLiteral] = {}
            self.parsed_variants: Dict[str, Tuple[List[parser.TypeLiteral], int]] = {}

            if isinstance(parsed, parser.Struct):
                self.parsed_field_types = parsed.fields

            if isinstance(parsed, parser.Enum):
                for i, item in enumerate(parsed.variants):
                    self.parsed_variants[item.name.name] = (item.associated_data, i)

    class Resolved:
        def __init__(
            self,
            fields: Dict[str, VariableType],
            enum_fields: Dict[str, Tuple[List[VariableType], int]],
        ) -> None:
            self.fields = fields
            self.enum_fields = enum_fields

    def __init__(
        self,
        parsed: parser.TypeLiteral | parser.Struct | parser.Enum,
        param_count: int,
    ) -> None:
        self.state: Type.Resolved | Type.Unresolved = Type.Unresolved(parsed)
        self.param_count = param_count
        super().__init__(parsed.position, parsed.identifier.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Type):
            return False

        return self.name == other.name and self.position == other.position

    @property
    def fields(self) -> Dict[str, VariableType]:
        assert isinstance(self.state, Type.Resolved)
        return self.state.fields

    @property
    def enum_fields(self) -> Dict[str, Tuple[List[VariableType], int]]:
        assert isinstance(self.state, Type.Resolved)
        return self.state.enum_fields

    def get_unresolved(self) -> Type.Unresolved:
        assert isinstance(self.state, Type.Unresolved)
        return self.state

    def resolve(
        self,
        fields: Dict[str, VariableType],
        enum_fields: Dict[str, Tuple[List[VariableType], int]],
    ) -> None:
        assert isinstance(self.state, Type.Unresolved)
        self.state = Type.Resolved(fields, enum_fields)

    def is_resolved(self) -> bool:
        return isinstance(self.state, Type.Resolved)

    def is_enum(self) -> bool:
        return bool(self.enum_fields)


class VariableType(AaaCrossReferenceModel):
    def __init__(
        self,
        type: Type,
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
    def __init__(self, name: str, position: Position) -> None:
        self.name = name
        super().__init__(position)


class CallFunction(FunctionBodyItem):
    def __init__(
        self, function: Function, type_params: List[VariableType], position: Position
    ) -> None:
        self.function = function
        self.type_params = type_params
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
        enum_type: Type,
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


class CrossReferencerOutput(AaaModel):
    def __init__(
        self,
        types: Dict[Tuple[Path, str], Type],
        functions: Dict[Tuple[Path, str], Function],
        imports: Dict[Tuple[Path, str], Import],
        builtins_path: Path,
        entrypoint: Path,
    ) -> None:
        self.types = types
        self.functions = functions
        self.imports = imports
        self.builtins_path = builtins_path
        self.entrypoint = entrypoint

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from aaa import AaaModel

if TYPE_CHECKING:
    from aaa.cross_referencer.exceptions import CrossReferenceBaseException

from lark.lexer import Token

from aaa.parser import models as parser
from aaa.parser.transformer import DUMMY_TOKEN


class AaaCrossReferenceModel(AaaModel):
    def __init__(self, *, file: Path, token: Token) -> None:
        self.file = file
        self.token = token


class Unresolved(AaaCrossReferenceModel):
    def __init__(self) -> None:
        super().__init__(file=Path("/dev/null"), token=DUMMY_TOKEN)


class Identifiable(AaaCrossReferenceModel):
    def __init__(self, *, file: Path, token: Token, name: str) -> None:
        self.__name = name
        super().__init__(file=file, token=token)

    def identify(self) -> Tuple[Path, str]:
        return (self.file, self.__name)

    @property
    def name(self) -> str:
        return self.__name


IdentifiablesDict = Dict[Tuple[Path, str], Identifiable]


class Function(Identifiable):
    def __init__(
        self,
        *,
        parsed: parser.Function,
        type_params: Dict[str, Type] | Unresolved,
        arguments: List[Argument] | Unresolved,
        return_types: List[VariableType] | Unresolved,
        body: FunctionBody | Unresolved,
    ) -> None:
        self.type_params = type_params
        self.arguments = arguments
        self.return_types = return_types
        self.body = body
        self.struct_name, self.func_name = parsed.get_names()
        self.parsed_type_params = parsed.type_params
        self.parsed_arguments = parsed.arguments
        self.parsed_return_types = parsed.return_types
        self.parsed_body = parsed.body

        if self.struct_name:
            name = f"{self.struct_name}:{self.func_name}"
        else:
            name = self.func_name

        super().__init__(file=parsed.file, token=parsed.token, name=name)

    def get_argument(self, name: str) -> Optional[Argument]:
        assert not isinstance(self.arguments, Unresolved)

        for argument in self.arguments:
            if name == argument.name:
                return argument
        return None

    def is_member_function(self) -> bool:
        return self.struct_name != ""

    def get_parsed_type_param(self, name: str) -> Optional[parser.TypeLiteral]:
        for parsed_type_param in self.parsed_type_params:
            if parsed_type_param.identifier.name == name:
                return parsed_type_param
        return None


class Argument(AaaCrossReferenceModel):
    def __init__(self, *, type: VariableType, name: str, file: Path) -> None:
        self.type = type
        self.name = name
        super().__init__(file=file, token=type.token)


class FunctionBodyItem(AaaCrossReferenceModel):
    ...


class FunctionBody(FunctionBodyItem):
    def __init__(
        self, *, parsed: parser.FunctionBody, items: List[FunctionBodyItem]
    ) -> None:
        self.items = items
        super().__init__(file=parsed.file, token=parsed.token)


class Import(Identifiable):
    def __init__(
        self,
        *,
        parsed: parser.ImportItem,
        source_file: Path,
        source_name: str,
        imported_name: str,
        source: Identifiable | Unresolved,
    ) -> None:
        self.source_file = source_file
        self.source_name = source_name
        self.imported_name = imported_name
        self.source = source
        super().__init__(file=parsed.file, token=parsed.token, name=self.imported_name)


class Type(Identifiable):
    def __init__(
        self,
        *,
        parsed: parser.TypeLiteral | parser.Struct,
        param_count: int,
        fields: Dict[str, VariableType] | Unresolved,
    ) -> None:
        self.param_count = param_count
        self.fields = fields
        self.parsed_field_types: Dict[str, parser.TypeLiteral] = {}

        if isinstance(parsed, parser.Struct):
            self.parsed_field_types = parsed.fields

        super().__init__(
            file=parsed.file,
            token=parsed.token,
            name=parsed.identifier.name,
        )


class VariableType(AaaCrossReferenceModel):
    def __init__(
        self,
        *,
        parsed: parser.TypeLiteral,
        type: Type,
        params: List[VariableType],
        is_placeholder: bool,
    ) -> None:
        self.type = type
        self.params = params
        self.is_placeholder = is_placeholder
        self.name = self.type.name
        super().__init__(file=parsed.file, token=parsed.token)

    def __repr__(self) -> str:
        output = self.name

        if self.params:
            output += "["
            for param in self.params:
                output += repr(param)
            output += "]"

        return output

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VariableType):
            return False

        # NOTE: Type instances are unique, we can use identity here
        if self.type is not other.type:
            return False

        return self.params == other.params


class IntegerLiteral(FunctionBodyItem):
    def __init__(self, *, parsed: parser.IntegerLiteral) -> None:
        self.value = parsed.value
        super().__init__(file=parsed.file, token=parsed.token)


class StringLiteral(FunctionBodyItem, parser.StringLiteral):
    def __init__(self, *, parsed: parser.StringLiteral) -> None:
        self.value = parsed.value
        super().__init__(file=parsed.file, token=parsed.token)


class BooleanLiteral(FunctionBodyItem, parser.BooleanLiteral):
    def __init__(self, *, parsed: parser.BooleanLiteral) -> None:
        self.value = parsed.value
        super().__init__(file=parsed.file, token=parsed.token)


class Operator(FunctionBodyItem, parser.Operator):
    def __init__(self, *, parsed: parser.Operator) -> None:
        self.value = parsed.value
        super().__init__(file=parsed.file, token=parsed.token)


class Loop(FunctionBodyItem):
    def __init__(
        self,
        *,
        condition: FunctionBody,
        body: FunctionBody,
        parsed: parser.Loop,
    ) -> None:
        self.condition = condition
        self.body = body
        super().__init__(file=parsed.file, token=parsed.token)


class IdentifierKind(AaaModel):
    ...


class IdentifierUsingArgument(IdentifierKind):
    def __init__(self, *, arg_type: VariableType) -> None:
        self.arg_type = arg_type


class IdentifierCallingFunction(IdentifierKind):
    def __init__(self, *, function: Function) -> None:
        self.function = function


class IdentifierCallingType(IdentifierKind):
    def __init__(self, *, type: Type) -> None:
        self.type = type


class Identifier(FunctionBodyItem):
    def __init__(
        self, *, kind: IdentifierKind | Unresolved, parsed: parser.Identifier
    ) -> None:
        self.kind = kind
        self.name = parsed.name
        super().__init__(file=parsed.file, token=parsed.token)


class Branch(FunctionBodyItem):
    def __init__(
        self,
        *,
        condition: FunctionBody,
        if_body: FunctionBody,
        else_body: FunctionBody,
        parsed: parser.Branch,
    ) -> None:
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body
        super().__init__(file=parsed.file, token=parsed.token)


class MemberFunctionName(FunctionBodyItem):
    def __init__(self, *, parsed: parser.MemberFunctionLiteral) -> None:
        self.struct_name = parsed.struct_name
        self.func_name = parsed.func_name
        super().__init__(file=parsed.file, token=parsed.token)


class StructFieldQuery(FunctionBodyItem):
    def __init__(self, *, parsed: parser.StructFieldQuery) -> None:
        self.field_name = parsed.field_name
        super().__init__(file=parsed.file, token=parsed.token)


class StructFieldUpdate(FunctionBodyItem):
    def __init__(
        self, *, parsed: parser.StructFieldUpdate, new_value_expr: FunctionBody
    ) -> None:
        self.field_name = parsed.field_name
        self.new_value_expr = new_value_expr
        super().__init__(file=parsed.file, token=parsed.token)


class CrossReferencerOutput(AaaModel):
    def __init__(
        self,
        *,
        types: Dict[Tuple[Path, str], Type],
        functions: Dict[Tuple[Path, str], Function],
        imports: Dict[Tuple[Path, str], Import],
        builtins_path: Path,
        exceptions: List[CrossReferenceBaseException],
    ) -> None:
        # TODO enforce somehow via typing that there is no Unresolved in instances of this type
        self.types = types
        self.functions = functions
        self.imports = imports
        self.exceptions = exceptions
        self.builtins_path = builtins_path

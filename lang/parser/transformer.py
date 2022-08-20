from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from lark.exceptions import UnexpectedInput
from lark.lexer import Token
from lark.visitors import Transformer, v_args

from lang.parser import aaa_keyword_parser
from lang.parser.exceptions import KeywordUsedAsIdentifier
from lang.parser.models import (
    AaaParseModel,
    Argument,
    BooleanLiteral,
    Branch,
    BranchCondition,
    BranchElseBody,
    BranchIfBody,
    Function,
    FunctionBody,
    FunctionBodyItem,
    Identifier,
    Import,
    ImportItem,
    IntegerLiteral,
    Loop,
    LoopBody,
    LoopCondition,
    MemberFunctionName,
    Operator,
    ParsedFile,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    TypeLiteral,
    TypePlaceholder,
)


@v_args(inline=True)
class AaaTransformer(Transformer[Any, ParsedFile]):
    def __init__(self, file: Path) -> None:
        self.file = file
        super().__init__()

    def argument_list(self, *arguments: Argument) -> List[Argument]:
        return list(arguments)

    @v_args(inline=False)
    def argument(
        self, args: Tuple[Identifier, TypeLiteral | TypePlaceholder]
    ) -> Argument:
        name_identifier, var_type = args
        return Argument(
            name=name_identifier.name,
            name_token=name_identifier.token,
            type=var_type,
        )

    def boolean(self, token: Token) -> BooleanLiteral:
        return BooleanLiteral(value=token.value)

    def branch(self, *args: List[AaaParseModel]) -> Branch:
        condition: FunctionBody
        if_body: FunctionBody
        else_body = FunctionBody(items=[])

        for arg in args:
            if isinstance(arg, BranchCondition):
                condition = arg.value
            elif isinstance(arg, BranchIfBody):
                if_body = arg.value
            elif isinstance(arg, BranchElseBody):
                else_body = arg.value
            else:  # pragma: nocover
                assert False

        return Branch(condition=condition, if_body=if_body, else_body=else_body)

    def branch_condition(self, function_body: FunctionBody) -> BranchCondition:
        return BranchCondition(value=function_body)

    def branch_if_body(self, function_body: FunctionBody) -> BranchIfBody:
        return BranchIfBody(value=function_body)

    def branch_else_body(self, function_body: FunctionBody) -> BranchElseBody:
        return BranchElseBody(value=function_body)

    @v_args(inline=False)
    def builtin_function_definition(self, args: List[Any]) -> Function:
        name: str | MemberFunctionName = ""
        arguments: List[Argument] = []
        return_types: List[TypeLiteral | TypePlaceholder] = []
        token: Token

        for arg in args:
            if isinstance(arg, StringLiteral):
                name = arg.value
            elif isinstance(arg, list):
                for item in arg:
                    if isinstance(item, Argument):
                        arguments.append(item)
                    elif isinstance(item, (TypePlaceholder, TypeLiteral)):
                        return_types.append(item)
                    else:  # pragma: nocover
                        assert False
            elif isinstance(arg, MemberFunctionName):
                name = arg
            elif isinstance(arg, Token):
                token = arg
            else:  # pragma: nocover
                assert False

        return Function(
            name=name,
            arguments=arguments,
            return_types=return_types,
            body=FunctionBody(items=[]),
            token=token,
        )

    def builtins_file_root(self, *functions: Function) -> ParsedFile:
        return ParsedFile(functions=list(functions), imports=[], structs=[])

    def function_body_item(
        self, function_body_item: FunctionBodyItem
    ) -> FunctionBodyItem:
        return function_body_item

    def function_body(self, *function_body_items: FunctionBodyItem) -> FunctionBody:
        return FunctionBody(items=list(function_body_items))

    @v_args(inline=False)
    def function_definition(self, args: List[Any]) -> Function:
        name: str | MemberFunctionName = ""
        body: FunctionBody
        arguments: List[Argument] = []
        return_types: List[TypeLiteral | TypePlaceholder] = []
        token: Token

        for arg in args:
            if isinstance(arg, Identifier):
                name = arg.name
            elif isinstance(arg, FunctionBody):
                body = arg
            elif isinstance(arg, list):
                for item in arg:
                    if isinstance(item, Argument):
                        arguments.append(item)
                    elif isinstance(item, (TypeLiteral, TypePlaceholder)):
                        return_types.append(item)
                    else:  # pragma: nocover
                        assert False
            elif isinstance(arg, MemberFunctionName):
                name = arg
            elif isinstance(arg, Token):
                token = arg
            else:  # pragma: nocover
                assert False

        return Function(
            name=name,
            arguments=arguments,
            return_types=return_types,
            body=body,
            token=token,
        )

    def function_arguments(self, args: List[Argument]) -> List[Argument]:
        return args

    def function_name(
        self, name: Union[Identifier, MemberFunctionName]
    ) -> Union[Identifier, MemberFunctionName]:
        return name

    def function_return_types(
        self, args: List[TypeLiteral | TypePlaceholder]
    ) -> List[TypeLiteral | TypePlaceholder]:
        return args

    def identifier(self, token: Token) -> Identifier:
        try:
            aaa_keyword_parser.parse(f"{token.value} ")
        except UnexpectedInput:
            return Identifier(name=token.value, token=token)
        else:
            # We're getting a keyword where we're expecting an identifier
            raise KeywordUsedAsIdentifier(token=token, file=self.file)

    def import_item(
        self, original_name: Identifier, imported_name: Optional[Identifier] = None
    ) -> ImportItem:
        if imported_name is None:
            imported_name = original_name

        return ImportItem(
            origninal_name=original_name.name, imported_name=imported_name.name
        )

    def import_items(self, *import_items: ImportItem) -> List[ImportItem]:
        return list(import_items)

    def import_statement(
        self, token: Token, source: StringLiteral, imported_items: List[ImportItem]
    ) -> Import:
        return Import(source=source.value, imported_items=imported_items, token=token)

    def integer(self, token: Token) -> IntegerLiteral:
        return IntegerLiteral(value=int(token.value))

    def literal(
        self, literal: Union[IntegerLiteral, BooleanLiteral, StringLiteral]
    ) -> Union[IntegerLiteral, BooleanLiteral, StringLiteral]:
        return literal

    def loop(self, condition: LoopCondition, body: LoopBody) -> Loop:
        return Loop(condition=condition.value, body=body.value)

    def loop_condition(self, function_body: FunctionBody) -> LoopCondition:
        return LoopCondition(value=function_body)

    def loop_body(self, function_body: FunctionBody) -> LoopBody:
        return LoopBody(value=function_body)

    def member_function_name(self, token: Token) -> Identifier:
        return Identifier(name=token.value, token=token)

    # TODO the token and function name needs to be improved
    def member_function(
        self, parsed_type: TypeLiteral | TypePlaceholder, func_name: Identifier
    ) -> MemberFunctionName:
        return MemberFunctionName(type_name=parsed_type.name, func_name=func_name.name)

    def operator(self, token: Token) -> Operator:
        return Operator(value=token.value)

    def regular_file_root(self, *args: Function | Struct | Import) -> ParsedFile:
        functions: List[Function] = []
        imports: List[Import] = []
        structs: List[Struct] = []

        for arg in args:
            if isinstance(arg, Function):
                functions.append(arg)
            elif isinstance(arg, Struct):
                structs.append(arg)
            elif isinstance(arg, Import):
                imports.append(arg)
            else:  # pragma: nocover
                assert False

        return ParsedFile(functions=functions, imports=imports, structs=structs)

    def return_types(
        self, *types: TypeLiteral | TypePlaceholder
    ) -> List[TypeLiteral | TypePlaceholder]:
        return list(types)

    def string(self, token: Token) -> StringLiteral:
        assert len(token.value) >= 2

        value = token.value[1:-1]
        value = value.replace("\\\\", "\\")
        value = value.replace("\\n", "\n")
        value = value.replace('\\"', '"')

        return StringLiteral(value=value)

    def struct_definition(
        self, token: Token, name: Identifier, field_list: List[Argument]
    ) -> Struct:
        fields = {field.name: field.type for field in field_list}
        return Struct(name=name.name, fields=fields, token=token)

    def struct_field_query_operator(self, token: Token) -> Token:
        return token

    def struct_field_query(
        self, field_name: StringLiteral, token: Token
    ) -> StructFieldQuery:
        return StructFieldQuery(field_name=field_name, operator_token=token)

    def struct_field_update_operator(self, token: Token) -> Token:
        return token

    def struct_field_update(
        self, field_name: StringLiteral, new_value_expr: FunctionBody, token: Token
    ) -> StructFieldUpdate:
        return StructFieldUpdate(
            field_name=field_name, new_value_expr=new_value_expr, operator_token=token
        )

    def struct_function_identifier(
        self, type_name: Identifier, func_name: Identifier
    ) -> MemberFunctionName:
        return MemberFunctionName(type_name=type_name.name, func_name=func_name.name)

    def type(
        self, type: TypeLiteral | TypePlaceholder
    ) -> TypeLiteral | TypePlaceholder:
        return type

    def type_literal(
        self,
        token: Token,
        type_params: Optional[List[TypeLiteral | TypePlaceholder]] = None,
    ) -> TypeLiteral:
        return TypeLiteral(name=token.value, token=token, params=type_params or [])

    def type_params(
        self, *args: TypeLiteral | TypePlaceholder
    ) -> List[TypeLiteral | TypePlaceholder]:
        return list(args)

    def type_placeholder(self, identifier: Identifier) -> TypePlaceholder:
        return TypePlaceholder(name=identifier.name, token=identifier.token)

from typing import Any, List, Optional, Tuple, Union

from lark.lexer import Token
from lark.visitors import Transformer, v_args

from lang.models.parse import (
    Argument,
    BooleanLiteral,
    Branch,
    BranchCondition,
    BranchElseBody,
    BranchIfBody,
    BuiltinFunction,
    BuiltinFunctionArguments,
    BuiltinFunctionReturnTypes,
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
    ParsedBuiltinsFile,
    ParsedFile,
    ParsedType,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
)


@v_args(inline=True)
class AaaTransformer(Transformer[Any, Any]):
    @v_args(inline=False)
    def argument_list(self, arguments: List[Argument]) -> List[Argument]:
        return arguments

    @v_args(inline=False)
    def argument(self, args: Tuple[Identifier, ParsedType]) -> Argument:
        name_identifier, parsed_type = args
        return Argument(
            name=name_identifier.name,
            name_token=name_identifier.token,
            type=parsed_type,
        )

    def boolean(self, token: Token) -> BooleanLiteral:
        return BooleanLiteral(value=token.value)

    def branch(self, *args: List[StructFieldQuery]) -> Branch:
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

    def builtin_function_definition(
        self, *args: List[StructFieldQuery]
    ) -> BuiltinFunction:
        arguments: List[ParsedType] = []
        return_types: List[ParsedType] = []
        name = ""

        for arg in args:
            if isinstance(arg, StringLiteral):
                name = arg.value
            elif isinstance(arg, BuiltinFunctionArguments):
                arguments = arg.value
            elif isinstance(arg, BuiltinFunctionReturnTypes):
                return_types = arg.value
            else:  # pragma: nocover
                assert False

        return BuiltinFunction(
            name=name, arguments=arguments, return_types=return_types
        )

    def builtin_function_arguments(
        self, arguments: List[ParsedType]
    ) -> BuiltinFunctionArguments:
        return BuiltinFunctionArguments(value=arguments)

    def builtin_function_return_types(
        self, arguments: List[ParsedType]
    ) -> BuiltinFunctionReturnTypes:
        return BuiltinFunctionReturnTypes(value=arguments)

    @v_args(inline=False)
    def builtins_file_root(self, args: List[BuiltinFunction]) -> ParsedBuiltinsFile:
        functions: List[BuiltinFunction] = []

        for arg in args:
            if isinstance(arg, BuiltinFunction):
                functions.append(arg)
            else:  # pragma: nocover
                assert False

        return ParsedBuiltinsFile(functions=functions)

    def function_body_item(
        self, function_body_item: FunctionBodyItem
    ) -> FunctionBodyItem:
        return function_body_item

    @v_args(inline=False)
    def function_body(self, args: List[FunctionBodyItem]) -> FunctionBody:
        return FunctionBody(items=args)

    @v_args(inline=False)
    def function_definition(self, args: List[StructFieldQuery]) -> Function:
        name: str | MemberFunctionName = ""
        body: FunctionBody
        arguments: List[Argument] = []
        return_types: List[ParsedType] = []
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
                    elif isinstance(item, ParsedType):
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

    def function_return_types(self, args: List[ParsedType]) -> List[ParsedType]:
        return args

    def identifier(self, token: Token) -> Identifier:
        return Identifier(name=token.value, token=token)

    def import_item(
        self, original_name: Identifier, imported_name: Optional[Identifier] = None
    ) -> ImportItem:
        if imported_name is None:
            imported_name = original_name

        return ImportItem(
            origninal_name=original_name.name, imported_name=imported_name.name
        )

    @v_args(inline=False)
    def import_items(self, import_items: List[ImportItem]) -> List[ImportItem]:
        assert all(isinstance(item, ImportItem) for item in import_items)
        return import_items

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
        self, parsed_type: ParsedType, func_name: Identifier
    ) -> MemberFunctionName:
        return MemberFunctionName(type_name=parsed_type.name, func_name=func_name.name)

    def operator(self, token: Token) -> Operator:
        return Operator(value=token.value)

    @v_args(inline=False)
    def regular_file_root(self, args: List[StructFieldQuery]) -> ParsedFile:
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

    @v_args(inline=False)
    def return_types(self, types: List[ParsedType]) -> List[ParsedType]:
        return types

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

    def type(self, type: ParsedType) -> ParsedType:
        return type

    @v_args(inline=False)
    def type_literal(self, args: List[Token | List[ParsedType]]) -> ParsedType:
        type_name = ""
        type_parameters: List[ParsedType] = []
        for arg in args:
            if isinstance(arg, Token):
                type_name = arg.value
            elif isinstance(arg, list):
                type_parameters = arg
            elif isinstance(arg, Identifier):
                type_name = arg.name
            else:  # pragma: nocover
                assert False

        return ParsedType(
            name=type_name, parameters=type_parameters, is_placeholder=False
        )

    @v_args(inline=False)
    def type_params(self, types: List[ParsedType]) -> List[ParsedType]:
        return types

    def type_placeholder(self, identifier: Identifier) -> ParsedType:
        return ParsedType(name=identifier.name, parameters=[], is_placeholder=True)

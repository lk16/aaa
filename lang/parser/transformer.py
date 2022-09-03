from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
    MemberFunctionLiteral,
    Operator,
    ParsedFile,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    TypeLiteral,
    TypeParameters,
)

DUMMY_TOKEN = Token(type_="", value="")  # type: ignore


@v_args(inline=True)
class AaaTransformer(Transformer[Any, ParsedFile]):
    def __init__(self, file: Path) -> None:
        self.file = file
        super().__init__()

    def arguments(self, *arguments: Argument) -> Dict[str, Argument]:
        argument_dict: Dict[str, Argument] = {}

        for argument in arguments:
            name = argument.identifier.name

            if name in argument_dict:
                # Argument name collision
                raise NotImplementedError

            argument_dict[name] = argument

        return argument_dict

    def argument(self, identifier: Identifier, type: TypeLiteral) -> Argument:
        return Argument(token=identifier.token, identifier=identifier, type=type)

    def boolean(self, token: Token) -> BooleanLiteral:
        return BooleanLiteral(token=token, value=token.value)

    def branch(self, *args: List[AaaParseModel]) -> Branch:
        condition: FunctionBody
        if_body: FunctionBody
        else_body = FunctionBody(token=DUMMY_TOKEN, items=[])

        for arg in args:
            if isinstance(arg, BranchCondition):
                condition = arg
            elif isinstance(arg, BranchIfBody):
                if_body = arg
            elif isinstance(arg, BranchElseBody):
                else_body = arg
            else:  # pragma: nocover
                assert False

        return Branch(
            token=condition.token,
            condition=condition,
            if_body=if_body,
            else_body=else_body,
        )

    def branch_condition(
        self, token: Token, function_body: FunctionBody
    ) -> BranchCondition:
        return BranchCondition(token=token, items=function_body.items)

    def branch_if_body(self, token: Token, function_body: FunctionBody) -> BranchIfBody:
        return BranchIfBody(token=token, items=function_body.items)

    def branch_else_body(
        self, else_token: Token, begin_token: Token, function_body: FunctionBody
    ) -> BranchElseBody:
        return BranchElseBody(token=begin_token, items=function_body.items)

    def builtin_type_declaration(
        self, token: Token, type_literal: TypeLiteral
    ) -> TypeLiteral:
        return type_literal

    @v_args(inline=False)
    def builtin_function_declaration(self, args: List[Any]) -> Function:
        for index, arg in enumerate(args):
            if isinstance(arg, Operator):
                args[index] = Identifier(token=arg.token, name=arg.value)

        args.append(FunctionBody(token=DUMMY_TOKEN, items=[]))

        function: Function = self.function_definition(args)
        return function

    def builtins_file_root(self, *args: Function | TypeLiteral) -> ParsedFile:
        functions: List[Function] = []
        types: List[TypeLiteral] = []

        for arg in args:
            if isinstance(arg, Function):
                functions.append(arg)
            elif isinstance(arg, TypeLiteral):
                types.append(arg)
            else:  # pragma: nocover
                assert False

        return ParsedFile(
            token=args[0].token,
            functions=functions,
            imports=[],
            structs=[],
            types=types,
        )

    def function_body_item(
        self, function_body_item: FunctionBodyItem
    ) -> FunctionBodyItem:
        return function_body_item

    def function_body(self, *function_body_items: FunctionBodyItem) -> FunctionBody:
        token = function_body_items[0].token
        return FunctionBody(token=token, items=list(function_body_items))

    @v_args(inline=False)
    def function_definition(self, args: List[Any]) -> Function:
        name: MemberFunctionLiteral | Identifier
        body: FunctionBody
        arguments: Dict[str, Argument] = {}
        return_types: List[TypeLiteral] = []
        type_params: List[TypeLiteral] = []
        token: Token

        for arg in args:
            if isinstance(arg, Identifier):
                name = arg
            elif isinstance(arg, FunctionBody):
                body = arg
            elif isinstance(arg, dict):
                arguments = arg
            elif isinstance(arg, list):
                for item in arg:
                    if isinstance(item, (TypeLiteral)):
                        return_types.append(item)
                    else:  # pragma: nocover
                        assert False
            elif isinstance(arg, MemberFunctionLiteral):
                name = arg
            elif isinstance(arg, Token):
                token = arg
            elif isinstance(arg, TypeParameters):
                type_params = arg.value
            else:  # pragma: nocover
                assert False

        return Function(
            token=token,
            name=name,
            arguments=arguments,
            type_params=type_params,
            return_types=return_types,
            body=body,
        )

    def function_arguments(self, args: List[Argument]) -> List[Argument]:
        return args

    def function_name(
        self, name: Union[Identifier, MemberFunctionLiteral]
    ) -> Union[Identifier, MemberFunctionLiteral]:
        return name

    def function_return_types(self, args: List[TypeLiteral]) -> List[TypeLiteral]:
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
            origninal_name=original_name.name,
            imported_name=imported_name.name,
            token=original_name.token,
        )

    def import_items(self, *import_items: ImportItem) -> List[ImportItem]:
        return list(import_items)

    def import_statement(
        self, token: Token, source: StringLiteral, imported_items: List[ImportItem]
    ) -> Import:
        return Import(source=source.value, imported_items=imported_items, token=token)

    def integer(self, token: Token) -> IntegerLiteral:
        return IntegerLiteral(token=token, value=int(token.value))

    def literal(
        self, literal: Union[IntegerLiteral, BooleanLiteral, StringLiteral]
    ) -> Union[IntegerLiteral, BooleanLiteral, StringLiteral]:
        return literal

    def loop(
        self, condition: LoopCondition, begin_token: Token, body: LoopBody
    ) -> Loop:
        return Loop(token=condition.token, condition=condition.value, body=body.value)

    def loop_condition(
        self, token: Token, function_body: FunctionBody
    ) -> LoopCondition:
        return LoopCondition(token=token, value=function_body)

    def loop_body(self, function_body: FunctionBody) -> LoopBody:
        return LoopBody(token=function_body.token, value=function_body)

    def member_function_name(self, token: Token) -> Identifier:
        return Identifier(name=token.value, token=token)

    def member_function_literal(
        self, struct_name: TypeLiteral, func_name: Identifier
    ) -> MemberFunctionLiteral:
        return MemberFunctionLiteral(
            struct_name=struct_name, func_name=func_name, token=struct_name.token
        )

    def operator(self, token: Token) -> Operator:
        return Operator(value=token.value, token=token)

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

        return ParsedFile(
            token=args[0].token,
            functions=functions,
            imports=imports,
            structs=structs,
            types=[],
        )

    def return_types(self, *types: TypeLiteral) -> List[TypeLiteral]:
        return list(types)

    def string(self, token: Token) -> StringLiteral:
        assert len(token.value) >= 2

        value = token.value[1:-1]
        value = value.replace("\\\\", "\\")
        value = value.replace("\\n", "\n")
        value = value.replace('\\"', '"')

        return StringLiteral(token=token, value=value)

    def struct_definition(
        self,
        struct_token: Token,
        identifier: Identifier,
        begin_token: Token,
        fields: Dict[str, Argument],
    ) -> Struct:
        return Struct(
            token=struct_token,
            identifier=identifier,
            fields={field_name: field.type for (field_name, field) in fields.items()},
        )

    def struct_field_query_operator(self, token: Token) -> Token:
        return token

    def struct_field_query(
        self, field_name: StringLiteral, token: Token
    ) -> StructFieldQuery:
        return StructFieldQuery(field_name=field_name, token=token)

    def struct_field_update_operator(self, token: Token) -> Token:
        return token

    def struct_field_update(
        self, field_name: StringLiteral, new_value_expr: FunctionBody, token: Token
    ) -> StructFieldUpdate:
        return StructFieldUpdate(
            field_name=field_name, new_value_expr=new_value_expr, token=token
        )

    def struct_function_identifier(
        self, type_name: TypeLiteral, func_name: Identifier
    ) -> MemberFunctionLiteral:
        return MemberFunctionLiteral(
            token=type_name.token, struct_name=type_name, func_name=func_name
        )

    def type_literal(
        self,
        identifier: Identifier,
        params: Optional[TypeParameters] = None,
    ) -> TypeLiteral:
        if not params:
            params = TypeParameters(token=DUMMY_TOKEN, value=[])

        return TypeLiteral(token=identifier.token, identifier=identifier, params=params)

    def type_params(self, *type_literals: TypeLiteral) -> TypeParameters:
        return TypeParameters(token=type_literals[0].token, value=list(type_literals))

    def builtin_type(self, token: Token) -> Identifier:
        return Identifier(name=str(token), token=token)

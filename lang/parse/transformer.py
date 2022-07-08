from typing import Any, List, Tuple, Union

from lark.lexer import Token
from lark.visitors import Transformer

from lang.parse.models import (
    AaaTreeNode,
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
    MemberFunction,
    Operator,
    ParsedBuiltinsFile,
    ParsedFile,
    ParsedType,
    ParsedTypePlaceholder,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    TypeLiteral,
)


class AaaTransformer(Transformer[Any, Any]):  # TODO find right type params here
    def argument_list(self, arguments: List[Argument]) -> List[Argument]:
        return arguments

    def argument(self, args: Tuple[Identifier, ParsedType]) -> Argument:
        name = args[0].name
        return Argument(name=name, type=args[1])

    def branch(self, args: List[AaaTreeNode]) -> Branch:
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
            else:
                assert False

        return Branch(condition=condition, if_body=if_body, else_body=else_body)

    def branch_condition(self, function_bodies: List[FunctionBody]) -> BranchCondition:
        assert len(function_bodies) == 1
        return BranchCondition(value=function_bodies[0])

    def branch_if_body(self, function_bodies: List[FunctionBody]) -> BranchIfBody:
        assert len(function_bodies) == 1
        return BranchIfBody(value=function_bodies[0])

    def branch_else_body(self, function_bodies: List[FunctionBody]) -> BranchElseBody:
        assert len(function_bodies) == 1
        return BranchElseBody(value=function_bodies[0])

    def builtin_function_definition(self, args: List[AaaTreeNode]) -> BuiltinFunction:
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
            else:
                assert False

        return BuiltinFunction(
            name=name, arguments=arguments, return_types=return_types
        )

    def builtin_function_arguments(
        self, arguments: List[List[ParsedType]]
    ) -> BuiltinFunctionArguments:
        assert len(arguments) == 1
        return BuiltinFunctionArguments(value=arguments[0])

    def builtin_function_return_types(
        self, arguments: List[List[ParsedType]]
    ) -> BuiltinFunctionReturnTypes:
        assert len(arguments) == 1
        return BuiltinFunctionReturnTypes(value=arguments[0])

    def builtins_file_root(self, args: List[BuiltinFunction]) -> ParsedBuiltinsFile:
        functions: List[BuiltinFunction] = []

        for arg in args:
            if isinstance(arg, BuiltinFunction):
                functions.append(arg)
            else:
                assert False

        return ParsedBuiltinsFile(functions=functions)

    def function_body_item(self, args: List[FunctionBodyItem]) -> FunctionBodyItem:
        assert len(args) == 1
        return args[0]

    def function_body(self, args: List[FunctionBodyItem]) -> FunctionBody:
        breakpoint()
        return FunctionBody(items=args)

    def function_definition(self, args: List[AaaTreeNode]) -> Function:
        name = ""
        body: FunctionBody
        arguments: List[Argument] = []
        return_types: List[ParsedType] = []

        for arg in args:
            if isinstance(arg, Identifier):
                name = arg.name
            elif isinstance(arg, FunctionBody):
                body = arg
            else:
                assert False

        return Function(
            name=name, arguments=arguments, return_types=return_types, body=body
        )

    def function_arguments(self, args: List[List[Argument]]) -> List[Argument]:
        assert len(args) == 1
        return args[0]

    def function_name(
        self, names: List[Union[Identifier, MemberFunction]]
    ) -> Union[Identifier, MemberFunction]:
        assert len(names) == 1
        assert isinstance(names[0], (Identifier, MemberFunction))
        return names[0]

    def function_return_types(self, args: List[List[ParsedType]]) -> List[ParsedType]:
        return args[0]

    def identifier(self, tokens: List[Token]) -> Identifier:
        assert len(tokens) == 1
        return Identifier(name=tokens[0].value)

    def import_item(self, args: List[Identifier]) -> ImportItem:
        assert len(args) <= 2
        original_name = args[0].name

        if len(args) == 1:
            imported_name = original_name
        else:
            imported_name = args[1].name

        return ImportItem(origninal_name=original_name, imported_name=imported_name)

    def integer(self, tokens: List[Token]) -> IntegerLiteral:
        assert len(tokens) == 1
        value = int(tokens[0].value)
        return IntegerLiteral(value=value)

    def literal(
        self, literals: List[Union[IntegerLiteral, BooleanLiteral, StringLiteral]]
    ) -> Union[
        IntegerLiteral, BooleanLiteral, StringLiteral
    ]:  # TODO create union alias
        assert len(literals) == 1
        return literals[0]

    def loop(self, args: List[AaaTreeNode]) -> Loop:
        condition: FunctionBody
        body: FunctionBody

        for arg in args:
            if isinstance(arg, LoopCondition):
                condition = arg.value
            elif isinstance(arg, LoopBody):
                body = arg.value
            else:
                assert False

        return Loop(condition=condition, body=body)

    def loop_condition(self, function_bodies: List[FunctionBody]) -> LoopCondition:
        assert len(function_bodies) == 1
        return LoopCondition(value=function_bodies[0])

    def loop_body(self, function_bodies: List[FunctionBody]) -> LoopBody:
        assert len(function_bodies) == 1
        return LoopBody(value=function_bodies[0])

    def member_function(self, args: Tuple[TypeLiteral, Identifier]) -> MemberFunction:
        type_name = args[0].type_name
        func_name = args[1].name
        return MemberFunction(type_name=type_name, func_name=func_name)

    def operator(self, tokens: List[Token]) -> Operator:
        assert len(tokens) == 1
        return Operator(value=tokens[0].value)

    def regular_file_root(self, args: List[AaaTreeNode]) -> ParsedFile:
        functions: List[Function] = []
        imports: List[Import] = []
        structs: List[Struct] = []

        for arg in args:
            if isinstance(arg, Function):
                functions.append(arg)
            else:
                assert False

        return ParsedFile(functions=functions, imports=imports, structs=structs)

    def return_types(
        self, types: List[Union[TypeLiteral, ParsedTypePlaceholder]]
    ) -> List[ParsedType]:
        return_types: List[ParsedType] = []
        for type in types:
            return_types.append(ParsedType(type=type))

        return return_types

    def string(self, tokens: List[Token]) -> StringLiteral:
        assert len(tokens) == 1
        raw_str = tokens[0].value
        assert len(raw_str) >= 2

        value = (
            raw_str[1:-1].replace("\\\\", "\\").replace("\\n", "\n").replace('\\"', '"')
        )
        return StringLiteral(value=value)

    def struct_definition(
        self, args: Tuple[List[Identifier], List[Argument]]
    ) -> Struct:
        assert len(args[0]) == 1
        name = args[0][0].name
        fields = args[1]

        return Struct(name=name, fields=fields)

    def struct_field_query(self, args: List[StringLiteral]) -> StructFieldQuery:
        assert len(args) == 1
        return StructFieldQuery(field_name=args[0])

    def struct_field_update(
        self, args: Tuple[StringLiteral, FunctionBody]
    ) -> StructFieldUpdate:
        new_value_expr = args[1]
        return StructFieldUpdate(field_name=args[0], new_value_expr=new_value_expr)

    def type(
        self, types: List[Union[TypeLiteral, ParsedTypePlaceholder]]
    ) -> Union[TypeLiteral, ParsedTypePlaceholder]:
        return types[0]

    def type_literal(self, args: List[Token | List[ParsedType]]) -> TypeLiteral:
        type_name = ""
        type_parameters: List[ParsedType] = []

        for arg in args:
            if isinstance(arg, Token):
                type_name = arg.value
            elif isinstance(arg, list):
                type_parameters = arg
            else:
                assert False

        return TypeLiteral(type_name=type_name, type_parameters=type_parameters)

    def type_params(self, types: List[ParsedType]) -> List[ParsedType]:
        type_params: List[ParsedType] = []
        for type in types:
            type_params.append(type)
        return type_params

    def type_placeholder(self, identifiers: List[Identifier]) -> ParsedTypePlaceholder:
        assert len(identifiers) == 1
        return ParsedTypePlaceholder(name=identifiers[0].name)

from typing import Any, List, Union

from lark.lexer import Token
from lark.tree import Tree
from lark.visitors import Transformer

from lang.parse.models import (
    AaaTreeNode,
    Argument,
    BooleanLiteral,
    BuiltinFunction,
    BuiltinFunctionArguments,
    BuiltinFunctionReturnTypes,
    Function,
    FunctionBody,
    FunctionBodyItem,
    Identifier,
    Import,
    IntegerLiteral,
    MemberFunction,
    Operator,
    ParsedBuiltinsFile,
    ParsedFile,
    ParsedType,
    ParsedTypePlaceholder,
    StringLiteral,
    Struct,
    TypeLiteral,
)


class AaaTransformer(Transformer[Any, Any]):  # TODO find right type params here
    def argument_list(self, *args):
        breakpoint()  # TODO

    def argument(self, *args):
        breakpoint()  # TODO

    def boolean(self, *args):
        breakpoint()  # TODO

    def branch(self, *args):
        breakpoint()  # TODO

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

    def function_body_item(self, *args):
        return args

    def function_body(self, items: List[List[List[FunctionBodyItem]]]) -> FunctionBody:
        return FunctionBody(items=[item[0][0] for item in items])

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

    def function_arguments(self, *args):
        breakpoint()  # TODO

    def function_name(
        self, names: List[Union[Identifier, MemberFunction]]
    ) -> Union[Identifier, MemberFunction]:
        assert len(names) == 1
        assert isinstance(names[0], (Identifier, MemberFunction))
        return names[0]

    def function_return_types(self, *args):
        breakpoint()  # TODO

    def identifier(self, tokens: List[Token]) -> Identifier:
        assert len(tokens) == 1
        return Identifier(name=tokens[0].value)

    def import_item(self, *args):
        breakpoint()  # TODO

    def import_items(self, *args):
        breakpoint()  # TODO

    def import_statement(self, *args):
        breakpoint()  # TODO

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

    def loop(self, *args):
        breakpoint()  # TODO

    def member_function(self, *args):
        breakpoint()  # TODO

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

    def return_types(self, trees: List[Tree[ParsedType]]) -> List[ParsedType]:
        return_types: List[ParsedType] = []
        for tree in trees:
            assert isinstance(tree, Tree)
            type = tree.children[0]
            assert isinstance(type, (TypeLiteral, ParsedTypePlaceholder))

            return_type = ParsedType(type=type)
            return_types.append(return_type)

        return return_types

    def string(self, tokens: List[Token]) -> StringLiteral:
        assert len(tokens) == 1
        raw_str = tokens[0].value
        assert len(raw_str) >= 2

        value = (
            raw_str[1:-1].replace("\\\\", "\\").replace("\\n", "\n").replace('\\"', '"')
        )
        return StringLiteral(value=value)

    def struct_definition(self, *args):
        breakpoint()  # TODO

    def struct_field_query(self, *args):
        breakpoint()  # TODO

    def struct_field_update(self, *args):
        breakpoint()  # TODO

    def struct_function_definition(self, *args):
        breakpoint()  # TODO

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

    def type_params(self, trees: List[ParsedType]) -> List[ParsedType]:
        type_params: List[ParsedType] = []
        for tree in trees:
            assert isinstance(tree, Tree)
            type = tree.children[0]
            assert isinstance(type, (TypeLiteral, ParsedTypePlaceholder))

            type_param = ParsedType(type=type)
            type_params.append(type_param)
        return type_params

    def type_placeholder(self, identifiers: List[Identifier]) -> ParsedTypePlaceholder:
        assert len(identifiers) == 1
        return ParsedTypePlaceholder(name=identifiers[0].name)

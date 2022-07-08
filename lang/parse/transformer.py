from typing import List

from lark.lexer import Token
from lark.tree import Tree
from lark.visitors import Transformer

from lang.parse.models import (
    AaaTreeNode,
    BuiltinFunction,
    BuiltinFunctionArguments,
    BuiltinFunctionReturnTypes,
    Identifier,
    IntegerLiteral,
    ParsedBuiltinsFile,
    ParsedType,
    ParsedTypePlaceholder,
    StringLiteral,
    TypeLiteral,
)


class AaaTransformer(Transformer):
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
        breakpoint()  # TODO

    def function_body(self, *args):
        breakpoint()  # TODO

    def function_definition(self, *args):
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
        return IntegerLiteral(value=tokens[0].value)

    def loop(self, *args):
        breakpoint()  # TODO

    def member_function(self, *args):
        breakpoint()  # TODO

    def operator(self, *args):
        breakpoint()  # TODO

    def regular_file_root(self, *args):
        breakpoint()  # TODO

    def return_types(self, trees: List[Tree]) -> List[ParsedType]:
        return_types: List[ParsedType] = []
        for tree in trees:
            assert isinstance(tree, Tree)
            return_type = ParsedType(type=tree.children[0])
            return_types.append(return_type)

        return return_types

    def string(self, tokens: List[Token]) -> StringLiteral:
        assert len(tokens) == 1
        return StringLiteral(value=tokens[0].value)

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

    def type_params(self, parsed_types: List[ParsedType]) -> List[ParsedType]:
        return parsed_types

    def type_placeholder(self, identifiers: List[Identifier]) -> ParsedTypePlaceholder:
        assert len(identifiers) == 1
        return ParsedTypePlaceholder(name=identifiers[0].name)

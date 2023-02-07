from pathlib import Path
from typing import List, Optional, Tuple

from aaa import Position
from aaa.parser.exceptions import (
    EndOfFileException,
    ParserBaseException,
    ParserException,
    UnhandledTopLevelToken,
)
from aaa.parser.models import (
    Argument,
    Assignment,
    BooleanLiteral,
    Branch,
    Call,
    ForeachLoop,
    Function,
    FunctionBody,
    FunctionBodyItem,
    FunctionName,
    Identifier,
    Import,
    ImportItem,
    IntegerLiteral,
    ParsedFile,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
    TypeLiteral,
    UseBlock,
    WhileLoop,
)
from aaa.tokenizer.models import Token, TokenType


class SingleFileParser:
    def __init__(self, file: Path, tokens: List[Token], verbose: bool) -> None:
        self.tokens = tokens
        self.file = file
        self.verbose = verbose

    def parse_builtins_file(self) -> ParsedFile:
        parsed_file, offset = self._parse_builtins_file_root(0)

        if offset != len(self.tokens):
            token = self.tokens[offset]
            raise UnhandledTopLevelToken(token.position, token.type)

        return parsed_file

    def parse_regular_file(self) -> ParsedFile:
        parsed_file, offset = self._parse_regular_file_root(0)

        if offset != len(self.tokens):
            token = self.tokens[offset]
            raise UnhandledTopLevelToken(token.position, token.type)

        return parsed_file

    def _peek_token(self, offset: int) -> Optional[Token]:
        try:
            return self.tokens[offset]
        except IndexError:
            return None

    def _token(self, offset: int, expected: List[TokenType]) -> Tuple[Token, int]:
        token = self._peek_token(offset)

        if not token:
            raise EndOfFileException(self.file)

        if token.type not in expected:
            raise ParserException(token.position, expected, token.type)

        return token, offset + 1

    def _parse_identifier(self, offset: int) -> Tuple[Identifier, int]:
        start_offset = offset

        token, offset = self._token(offset, [TokenType.IDENTIFIER])
        identifier = Identifier(token.position, token.value)

        self._print_parse_tree_node("Identifier", start_offset, offset)
        return identifier, offset

    def _parse_flat_type_params(self, offset: int) -> Tuple[List[TypeLiteral], int]:
        start_offset = offset
        _, offset = self._token(offset, [TokenType.TYPE_PARAM_BEGIN])

        identifiers: List[Identifier] = []
        token: Optional[Token]

        while True:
            identifier, offset = self._parse_identifier(offset)
            identifiers.append(identifier)

            token, offset = self._token(
                offset, [TokenType.TYPE_PARAM_END, TokenType.COMMA]
            )

            if token.type == TokenType.TYPE_PARAM_END:
                break

            # Handle comma at the end, for example `[A,]` or `[A,B,]`
            token = self._peek_token(offset)
            if token and token.type == TokenType.TYPE_PARAM_END:
                _, offset = self._token(offset, [TokenType.TYPE_PARAM_END])
                break

        type_params = [
            TypeLiteral(identifier.position, identifier, [], False)
            for identifier in identifiers
        ]

        self._print_parse_tree_node("TypeParams", start_offset, offset)
        return type_params, offset

    def _parse_flat_type_literal(self, offset: int) -> Tuple[TypeLiteral, int]:
        start_offset = offset

        identifier, offset = self._parse_identifier(offset)

        type_params: List[TypeLiteral] = []

        try:
            type_params, offset = self._parse_flat_type_params(offset)
        except ParserBaseException:
            pass

        self._print_parse_tree_node("FlatTypeLiteral", start_offset, offset)
        type_literal = TypeLiteral(identifier.position, identifier, type_params, False)
        return type_literal, offset

    def _parse_type_declaration(self, offset: int) -> Tuple[TypeLiteral, int]:
        start_offset = offset

        _, offset = self._token(offset, [TokenType.TYPE])
        self._print_parse_tree_node("TypeLiteral", start_offset, offset)
        type_literal, offset = self._parse_flat_type_literal(offset)
        return type_literal, offset

    def _parse_function_name(self, offset: int) -> Tuple[FunctionName, int]:
        start_offset = offset

        type_literal, offset = self._parse_flat_type_literal(offset)
        identifier: Optional[Identifier] = None

        token = self._peek_token(offset)

        if token and token.type == TokenType.COLON:
            _, offset = self._token(offset, [TokenType.COLON])
            identifier, offset = self._parse_identifier(offset)

        struct_name: Optional[Identifier] = None

        if identifier:
            # member function name as in a declaration, such as `vec[T]:clear`
            struct_name = type_literal.identifier
            func_name = identifier

        else:
            # function name as in declaration, such as `dup[A]`
            func_name = type_literal.identifier

        function_name = FunctionName(
            type_literal.position, struct_name, type_literal.params, func_name
        )

        self._print_parse_tree_node("FunctionName", start_offset, offset)
        return function_name, offset

    def _parse_type_params(self, offset: int) -> Tuple[List[TypeLiteral], int]:
        start_offset = offset

        _, offset = self._token(offset, [TokenType.TYPE_PARAM_BEGIN])

        type_params: List[TypeLiteral] = []
        token: Optional[Token]

        while True:
            type_param, offset = self._parse_type_literal(offset)
            type_params.append(type_param)

            token, offset = self._token(
                offset, [TokenType.TYPE_PARAM_END, TokenType.COMMA]
            )

            if token.type == TokenType.TYPE_PARAM_END:
                break

            # Handle comma at the end, for example `[A,]` or `[A,B[C,],]`
            token = self._peek_token(offset)
            if token and token.type == TokenType.TYPE_PARAM_END:
                _, offset = self._token(offset, [TokenType.TYPE_PARAM_END])
                break

        self._print_parse_tree_node("TypeParams", start_offset, offset)
        return type_params, offset

    def _parse_type_literal(self, offset: int) -> Tuple[TypeLiteral, int]:
        start_offset = offset

        token = self._peek_token(offset)
        const = False

        if token and token.type == TokenType.CONST:
            _, offset = self._token(offset, [TokenType.CONST])
            const = True

        identifier, offset = self._parse_identifier(offset)

        type_params: List[TypeLiteral] = []

        try:
            type_params, offset = self._parse_type_params(offset)
        except ParserBaseException:
            pass

        type_literal = TypeLiteral(identifier.position, identifier, type_params, const)
        self._print_parse_tree_node("TypeLiteral", start_offset, offset)
        return type_literal, offset

    def _parse_argument(self, offset: int) -> Tuple[Argument, int]:
        start_offset = offset

        identifier, offset = self._parse_identifier(offset)
        _, offset = self._token(offset, [TokenType.AS])
        type, offset = self._parse_type_literal(offset)

        argument = Argument(identifier.position, identifier, type)
        self._print_parse_tree_node("Argument", start_offset, offset)
        return argument, offset

    def _parse_arguments(self, offset: int) -> Tuple[List[Argument], int]:
        start_offset = offset

        arguments: List[Argument] = []

        argument, offset = self._parse_argument(offset)
        arguments.append(argument)

        while True:
            try:
                _, offset = self._token(offset, [TokenType.COMMA])
            except ParserBaseException:
                break

            try:
                argument, offset = self._parse_argument(offset)
            except ParserBaseException:
                break
            else:
                arguments.append(argument)

        self._print_parse_tree_node("Arguments", start_offset, offset)
        return arguments, offset

    def _parse_return_types(self, offset: int) -> Tuple[List[TypeLiteral], int]:
        start_offset = offset

        return_types: List[TypeLiteral] = []

        return_type, offset = self._parse_type_literal(offset)
        return_types.append(return_type)

        while True:
            try:
                _, offset = self._token(offset, [TokenType.COMMA])
            except ParserBaseException:
                break

            try:
                return_type, offset = self._parse_type_literal(offset)
            except ParserBaseException:
                break
            else:
                return_types.append(return_type)

        self._print_parse_tree_node("ReturnTypes", start_offset, offset)
        return return_types, offset

    def _parse_function_declaration(self, offset: int) -> Tuple[Function, int]:
        start_offset = offset

        fn_token, offset = self._token(offset, [TokenType.FUNCTION])
        function_name, offset = self._parse_function_name(offset)
        arguments: List[Argument] = []
        return_types: List[TypeLiteral] = []

        token = self._peek_token(offset)
        if token and token.type == TokenType.ARGS:
            _, offset = self._token(offset, [TokenType.ARGS])
            arguments, offset = self._parse_arguments(offset)

        token = self._peek_token(offset)
        if token and token.type == TokenType.RETURN:
            _, offset = self._token(offset, [TokenType.RETURN])
            return_types, offset = self._parse_return_types(offset)

        function = Function(
            position=fn_token.position,
            struct_name=function_name.struct_name,
            func_name=function_name.func_name,
            type_params=function_name.type_params,
            arguments=arguments,
            return_types=return_types,
            body=None,
        )

        self._print_parse_tree_node("FunctionDeclaration", start_offset, offset)
        return function, offset

    def _parse_builtins_file_root(self, offset: int) -> Tuple[ParsedFile, int]:
        start_offset = offset

        first_token = self._peek_token(offset)

        if first_token:
            position = first_token.position
        else:
            position = Position(self.file, 1, 1)

        functions: List[Function] = []
        types: List[TypeLiteral] = []

        while True:
            try:
                function, offset = self._parse_function_declaration(offset)
            except ParserBaseException:
                pass
            else:
                functions.append(function)
                continue

            try:
                type, offset = self._parse_type_declaration(offset)
            except ParserBaseException:
                pass
            else:
                types.append(type)
                continue

            break

        parsed_file = ParsedFile(
            position=position,
            functions=functions,
            imports=[],
            structs=[],
            types=types,
        )

        self._print_parse_tree_node("ParsedFile", start_offset, offset)
        return parsed_file, offset

    def _parse_struct_definition(self, offset: int) -> Tuple[Struct, int]:
        start_offset = offset

        struct_token, offset = self._token(offset, [TokenType.STRUCT])
        identifier, offset = self._parse_identifier(offset)
        _, offset = self._token(offset, [TokenType.BEGIN])
        fields, offset = self._parse_arguments(offset)
        _, offset = self._token(offset, [TokenType.END])

        struct = Struct(
            position=struct_token.position,
            identifier=identifier,
            fields={field.identifier.name: field.type for field in fields},
        )

        self._print_parse_tree_node("StructDefinition", start_offset, offset)
        return struct, offset

    def _parse_string(self, offset: int) -> Tuple[StringLiteral, int]:
        start_offset = offset

        token, offset = self._token(offset, [TokenType.STRING])

        value = token.value[1:-1]
        value = value.replace("\\\\", "\\")
        value = value.replace("\\n", "\n")
        value = value.replace("\\r", "\r")
        value = value.replace('\\"', '"')

        string = StringLiteral(token.position, value)
        self._print_parse_tree_node("String", start_offset, offset)
        return string, offset

    def _parse_import_item(self, offset: int) -> Tuple[ImportItem, int]:
        start_offset = offset

        original, offset = self._parse_identifier(offset)

        token = self._peek_token(offset)
        if token and token.type == TokenType.AS:
            _, offset = self._token(offset, [TokenType.AS])
            imported, offset = self._parse_identifier(offset)
        else:
            imported = original

        import_item = ImportItem(
            position=original.position, origninal=original, imported=imported
        )

        self._print_parse_tree_node("ImportItem", start_offset, offset)
        return import_item, offset

    def _parse_import_items(self, offset: int) -> Tuple[List[ImportItem], int]:
        start_offset = offset

        import_items: List[ImportItem] = []

        import_item, offset = self._parse_import_item(offset)
        import_items.append(import_item)

        while True:
            try:
                _, offset = self._token(offset, [TokenType.COMMA])
            except ParserBaseException:
                break

            try:
                import_item, offset = self._parse_import_item(offset)
            except ParserBaseException:
                break
            else:
                import_items.append(import_item)

        self._print_parse_tree_node("ImportItems", start_offset, offset)
        return import_items, offset

    def _parse_import_statement(self, offset: int) -> Tuple[Import, int]:
        start_offset = offset

        from_token, offset = self._token(offset, [TokenType.FROM])
        source, offset = self._parse_string(offset)
        _, offset = self._token(offset, [TokenType.IMPORT])
        import_items, offset = self._parse_import_items(offset)

        import_ = Import(
            position=from_token.position,
            source=source.value,
            imported_items=import_items,
        )

        self._print_parse_tree_node("Import", start_offset, offset)
        return import_, offset

    def _parse_boolean(self, offset: int) -> Tuple[BooleanLiteral, int]:
        start_offset = offset

        token, offset = self._token(offset, [TokenType.TRUE, TokenType.FALSE])
        boolean = BooleanLiteral(token.position, token.value == "true")

        self._print_parse_tree_node("BooleanLiteral", start_offset, offset)
        return boolean, offset

    def _parse_integer(self, offset: int) -> Tuple[IntegerLiteral, int]:
        start_offset = offset

        token, offset = self._token(offset, [TokenType.INTEGER])

        integer = IntegerLiteral(token.position, int(token.value))
        self._print_parse_tree_node("IntegerLiteral", start_offset, offset)
        return integer, offset

    def _parse_call(self, offset: int) -> Tuple[Call, int]:
        start_offset = offset

        token: Optional[Token]
        identifier, offset = self._parse_identifier(offset)

        type_params: List[TypeLiteral] = []
        struct_name: Optional[Identifier] = None
        func_name: Identifier

        token = self._peek_token(offset)

        if token and token.type == TokenType.TYPE_PARAM_BEGIN:
            func_name = identifier
            type_params, offset = self._parse_type_params(offset)
        elif token and token.type == TokenType.COLON:
            _, offset = self._token(offset, [TokenType.COLON])
            struct_name = identifier
            func_name, offset = self._parse_identifier(offset)
        else:
            func_name = identifier

        func_call = Call(identifier.position, struct_name, type_params, func_name)
        self._print_parse_tree_node("FunctionCall", start_offset, offset)
        return func_call, offset

    def _parse_branch(self, offset: int) -> Tuple[Branch, int]:
        start_offset = offset

        if_token, offset = self._token(offset, [TokenType.IF])
        condition, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.BEGIN])
        if_body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.END])

        token = self._peek_token(offset)
        else_body: Optional[FunctionBody] = None

        if token and token.type == TokenType.ELSE:
            _, offset = self._token(offset, [TokenType.ELSE])
            _, offset = self._token(offset, [TokenType.BEGIN])
            else_body, offset = self._parse_function_body(offset)
            _, offset = self._token(offset, [TokenType.END])

        branch = Branch(if_token.position, condition, if_body, else_body)

        self._print_parse_tree_node("Branch", start_offset, offset)
        return branch, offset

    def _parse_while_loop(self, offset: int) -> Tuple[WhileLoop, int]:
        start_offset = offset

        while_token, offset = self._token(offset, [TokenType.WHILE])
        condition, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.BEGIN])
        body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.END])

        while_loop = WhileLoop(while_token.position, condition, body)
        self._print_parse_tree_node("WhileLoop", start_offset, offset)
        return while_loop, offset

    def _parse_struct_field_query(self, offset: int) -> Tuple[StructFieldQuery, int]:
        start_offset = offset

        field_name, offset = self._parse_string(offset)
        _, offset = self._token(offset, [TokenType.GET_FIELD])

        field_query = StructFieldQuery(field_name.position, field_name)

        self._print_parse_tree_node("StructFieldQuery", start_offset, offset)
        return field_query, offset

    def _parse_struct_field_update(self, offset: int) -> Tuple[StructFieldUpdate, int]:
        start_offset = offset

        field_name, offset = self._parse_string(offset)
        _, offset = self._token(offset, [TokenType.BEGIN])
        new_value_expr, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.END])
        _, offset = self._token(offset, [TokenType.SET_FIELD])

        field_update = StructFieldUpdate(
            field_name.position, field_name, new_value_expr
        )
        self._print_parse_tree_node("StructFieldUpdate", start_offset, offset)
        return field_update, offset

    def _parse_function_body_item(self, offset: int) -> Tuple[FunctionBodyItem, int]:
        start_offset = offset
        token = self._peek_token(offset)
        next_token = self._peek_token(offset + 1)
        item: FunctionBodyItem

        if not token:
            raise EndOfFileException(self.file)

        if token.type == TokenType.STRING:
            if next_token and next_token.type == TokenType.GET_FIELD:
                item, offset = self._parse_struct_field_query(offset)
            elif next_token and next_token.type == TokenType.BEGIN:
                item, offset = self._parse_struct_field_update(offset)
            else:
                item, offset = self._parse_string(offset)

        elif token.type in [TokenType.TRUE, TokenType.FALSE]:
            item, offset = self._parse_boolean(offset)

        elif token.type == TokenType.INTEGER:
            item, offset = self._parse_integer(offset)

        elif token.type == TokenType.IDENTIFIER:
            if next_token and next_token.type in [TokenType.COMMA, TokenType.ASSIGN]:
                item, offset = self._parse_assignment(offset)
            else:
                item, offset = self._parse_call(offset)

        elif token.type == TokenType.IF:
            item, offset = self._parse_branch(offset)
        elif token.type == TokenType.WHILE:
            item, offset = self._parse_while_loop(offset)
        elif token.type == TokenType.FOREACH:
            item, offset = self._parse_foreach_loop(offset)
        elif token.type == TokenType.USE:
            item, offset = self._parse_use_block(offset)

        else:
            raise ParserException(
                position=token.position,
                expected_token_types=[
                    TokenType.FALSE,
                    TokenType.FOREACH,
                    TokenType.IDENTIFIER,
                    TokenType.IF,
                    TokenType.INTEGER,
                    TokenType.STRING,
                    TokenType.TRUE,
                    TokenType.WHILE,
                    TokenType.USE,
                ],
                found_token_type=token.type,
            )

        self._print_parse_tree_node("FunctionBodyItem", start_offset, offset)
        return item, offset

    def _parse_function_body(self, offset: int) -> Tuple[FunctionBody, int]:
        start_offset = offset

        items: List[FunctionBodyItem] = []

        item, offset = self._parse_function_body_item(offset)
        items.append(item)

        while True:
            try:
                item, offset = self._parse_function_body_item(offset)
            except ParserBaseException:
                break

            items.append(item)

        function_body = FunctionBody(items[0].position, items)
        self._print_parse_tree_node("FunctionBody", start_offset, offset)
        return function_body, offset

    def _parse_function_definition(self, offset: int) -> Tuple[Function, int]:
        start_offset = offset

        function, offset = self._parse_function_declaration(offset)
        _, offset = self._token(offset, [TokenType.BEGIN])
        body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.END])

        function.body = body
        self._print_parse_tree_node("FunctionDefinition", start_offset, offset)
        return function, offset

    def _parse_regular_file_root(self, offset: int) -> Tuple[ParsedFile, int]:
        start_offset = offset

        first_token = self._peek_token(offset)

        if first_token:
            position = first_token.position
        else:
            position = Position(self.file, 1, 1)

        functions: List[Function] = []
        structs: List[Struct] = []
        imports: List[Import] = []

        while True:
            token = self._peek_token(offset)

            if not token:
                break

            if token.type == TokenType.FUNCTION:
                function, offset = self._parse_function_definition(offset)
                functions.append(function)
            elif token.type == TokenType.STRUCT:
                struct, offset = self._parse_struct_definition(offset)
                structs.append(struct)
            elif token.type == TokenType.FROM:
                import_, offset = self._parse_import_statement(offset)
                imports.append(import_)
            else:
                break

        parsed_file = ParsedFile(
            position=position,
            functions=functions,
            imports=imports,
            structs=structs,
            types=[],
        )

        self._print_parse_tree_node("ParsedFileRoot", start_offset, offset)
        return parsed_file, offset

    def _parse_foreach_loop(self, offset: int) -> Tuple[ForeachLoop, int]:
        start_offset = offset

        foreach_token, offset = self._token(offset, [TokenType.FOREACH])
        _, offset = self._token(offset, [TokenType.BEGIN])
        body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.END])

        foreach = ForeachLoop(foreach_token.position, body)
        self._print_parse_tree_node("ForeachLoop", start_offset, offset)
        return foreach, offset

    def _parse_variables(self, offset: int) -> Tuple[List[Identifier], int]:
        start_offset = offset

        identifiers: List[Identifier] = []
        token: Optional[Token]

        identifier, offset = self._parse_identifier(offset)
        identifiers.append(identifier)

        while True:
            token = self._peek_token(offset)
            if not token or token.type != TokenType.COMMA:
                break

            _, offset = self._token(offset, [TokenType.COMMA])

            token = self._peek_token(offset)
            if not token or token.type != TokenType.IDENTIFIER:
                break

            identifier, offset = self._parse_identifier(offset)
            identifiers.append(identifier)

        self._print_parse_tree_node("Variables", start_offset, offset)
        return identifiers, offset

    def _parse_use_block(self, offset: int) -> Tuple[UseBlock, int]:
        start_offset = offset
        use_token, offset = self._token(offset, [TokenType.USE])
        variables, offset = self._parse_variables(offset)
        _, offset = self._token(offset, [TokenType.BEGIN])
        body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.END])

        use_block = UseBlock(use_token.position, variables, body)
        self._print_parse_tree_node("UseBlock", start_offset, offset)
        return use_block, offset

    def _parse_assignment(self, offset: int) -> Tuple[Assignment, int]:
        start_offset = offset

        variables, offset = self._parse_variables(offset)
        _, offset = self._token(offset, [TokenType.ASSIGN])
        _, offset = self._token(offset, [TokenType.BEGIN])
        body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.END])

        assignment = Assignment(variables[0].position, variables, body)
        self._print_parse_tree_node("Assignment", start_offset, offset)
        return assignment, offset

    def _print_parse_tree_node(
        self, kind: str, start_token_offset: int, end_token_offset: int
    ) -> None:  # pragma: nocover
        if not self.verbose:
            return

        tokens = self.tokens[start_token_offset:end_token_offset]
        tokens_joined = " ".join(token.value for token in tokens)
        print(f"parser | {kind:>20} | {tokens_joined}")

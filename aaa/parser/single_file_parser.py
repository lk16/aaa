from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
    CaseBlock,
    CaseLabel,
    DefaultBlock,
    Enum,
    EnumVariant,
    ForeachLoop,
    Function,
    FunctionBody,
    FunctionBodyItem,
    FunctionCall,
    FunctionName,
    FunctionPointerTypeLiteral,
    GetFunctionPointer,
    Identifier,
    Import,
    ImportItem,
    IntegerLiteral,
    MatchBlock,
    Never,
    ParsedFile,
    Return,
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
            raise ParserException(token, expected)

        return token, offset + 1

    def _parse_identifier(self, offset: int) -> Tuple[Identifier, int]:
        start_offset = offset

        token, offset = self._token(offset, [TokenType.IDENTIFIER])
        identifier = Identifier(token.position, token.value)

        self._print_parse_tree_node("Identifier", start_offset, offset)
        return identifier, offset

    def _parse_flat_type_params(self, offset: int) -> Tuple[List[TypeLiteral], int]:
        start_offset = offset
        _, offset = self._token(offset, [TokenType.SQUARE_BRACKET_OPEN])

        identifiers: List[Identifier] = []
        token: Optional[Token]

        while True:
            identifier, offset = self._parse_identifier(offset)
            identifiers.append(identifier)

            token, offset = self._token(
                offset, [TokenType.SQUARE_BRACKET_CLOSE, TokenType.COMMA]
            )

            if token.type == TokenType.SQUARE_BRACKET_CLOSE:
                break

            # Handle comma at the end, for example `[A,]` or `[A,B,]`
            token = self._peek_token(offset)
            if token and token.type == TokenType.SQUARE_BRACKET_CLOSE:
                _, offset = self._token(offset, [TokenType.SQUARE_BRACKET_CLOSE])
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

        _, offset = self._token(offset, [TokenType.SQUARE_BRACKET_OPEN])

        type_params: List[TypeLiteral] = []
        token: Optional[Token]

        while True:
            type_param, offset = self._parse_type_literal(offset)
            type_params.append(type_param)

            token, offset = self._token(
                offset, [TokenType.SQUARE_BRACKET_CLOSE, TokenType.COMMA]
            )

            if token.type == TokenType.SQUARE_BRACKET_CLOSE:
                break

            # Handle comma at the end, for example `[A,]` or `[A,B[C,],]`
            token = self._peek_token(offset)
            if token and token.type == TokenType.SQUARE_BRACKET_CLOSE:
                _, offset = self._token(offset, [TokenType.SQUARE_BRACKET_CLOSE])
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

    def _parse_comma_separated_type_list(
        self, offset: int
    ) -> Tuple[List[TypeLiteral | FunctionPointerTypeLiteral], int]:
        types: List[TypeLiteral | FunctionPointerTypeLiteral] = []

        while True:
            type: TypeLiteral | FunctionPointerTypeLiteral

            try:
                type, offset = self._parse_type_literal(offset)
            except ParserBaseException:
                try:
                    type, offset = self._parse_function_pointer_type_literal(offset)
                except ParserBaseException:
                    break

            types.append(type)

            token = self._peek_token(offset)

            if not token:
                raise EndOfFileException(self.file)

            if token.type == TokenType.COMMA:
                _, offset = self._token(offset, [TokenType.COMMA])

        return types, offset

    def _parse_function_pointer_type_literal(
        self, offset: int
    ) -> Tuple[FunctionPointerTypeLiteral, int]:
        start_offset = offset
        fn_token, offset = self._token(offset, [TokenType.FUNCTION])

        _, offset = self._token(offset, [TokenType.SQUARE_BRACKET_OPEN])
        argument_types, offset = self._parse_comma_separated_type_list(offset)
        _, offset = self._token(offset, [TokenType.SQUARE_BRACKET_CLOSE])

        _, offset = self._token(offset, [TokenType.SQUARE_BRACKET_OPEN])
        return_types, offset = self._parse_comma_separated_type_list(offset)
        _, offset = self._token(offset, [TokenType.SQUARE_BRACKET_CLOSE])

        function_pointer_type_literal = FunctionPointerTypeLiteral(
            fn_token.position, argument_types, return_types
        )
        self._print_parse_tree_node("FunctionPointerTypeLiteral", start_offset, offset)
        return function_pointer_type_literal, offset

    def _parse_type_or_function_pointer_literal(
        self, offset: int
    ) -> Tuple[TypeLiteral | FunctionPointerTypeLiteral, int]:
        token = self._peek_token(offset)

        if not token:
            raise EndOfFileException(self.file)

        if token.type == TokenType.FUNCTION:
            return self._parse_function_pointer_type_literal(offset)
        else:
            return self._parse_type_literal(offset)

    def _parse_argument(self, offset: int) -> Tuple[Argument, int]:
        start_offset = offset

        identifier, offset = self._parse_identifier(offset)
        _, offset = self._token(offset, [TokenType.AS])

        type, offset = self._parse_type_or_function_pointer_literal(offset)

        argument = Argument(identifier, type)
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

    def _parse_return_types(self, offset: int) -> Tuple[List[TypeLiteral] | Never, int]:
        start_offset = offset

        token = self._peek_token(offset)

        if token and token.type == TokenType.NEVER:
            never_token, offset = self._token(offset, [TokenType.NEVER])
            never = Never(never_token.position)
            return never, offset

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
        return_types: List[TypeLiteral] | Never = []

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
            end_position=None,
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
            enums=[],
        )

        self._print_parse_tree_node("ParsedFile", start_offset, offset)
        return parsed_file, offset

    def _parse_struct_field(self, offset: int) -> Tuple[str, TypeLiteral, int]:
        name, offset = self._parse_identifier(offset)
        _, offset = self._token(offset, [TokenType.AS])
        type, offset = self._parse_type_literal(offset)
        return name.name, type, offset

    def _parse_struct_fields(self, offset: int) -> Tuple[Dict[str, TypeLiteral], int]:
        fields: Dict[str, TypeLiteral] = {}

        while True:
            try:
                name, type, offset = self._parse_struct_field(offset)
            except ParserBaseException:
                break
            else:
                fields[name] = type

            try:
                _, offset = self._token(offset, [TokenType.COMMA])
            except ParserBaseException:
                break

        return fields, offset

    def _parse_struct_definition(self, offset: int) -> Tuple[Struct, int]:
        start_offset = offset

        struct_token, offset = self._token(offset, [TokenType.STRUCT])
        identifier, offset = self._parse_identifier(offset)
        _, offset = self._token(offset, [TokenType.BLOCK_START])
        fields, offset = self._parse_struct_fields(offset)
        _, offset = self._token(offset, [TokenType.BLOCK_END])

        struct = Struct(struct_token.position, identifier, fields)
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

    def _parse_function_call(self, offset: int) -> Tuple[FunctionCall, int]:
        start_offset = offset

        token: Optional[Token]
        identifier, offset = self._parse_identifier(offset)

        type_params: List[TypeLiteral] = []
        struct_name: Optional[Identifier] = None
        func_name: Identifier

        token = self._peek_token(offset)

        if token and token.type == TokenType.SQUARE_BRACKET_OPEN:
            func_name = identifier
            type_params, offset = self._parse_type_params(offset)
        elif token and token.type == TokenType.COLON:
            _, offset = self._token(offset, [TokenType.COLON])
            struct_name = identifier
            func_name, offset = self._parse_identifier(offset)
        else:
            func_name = identifier

        func_call = FunctionCall(
            identifier.position, struct_name, type_params, func_name
        )
        self._print_parse_tree_node("FunctionCall", start_offset, offset)
        return func_call, offset

    def _parse_case_label(self, offset: int) -> Tuple[CaseLabel, int]:
        start_offset = offset

        enum_name, offset = self._parse_identifier(offset)
        _, offset = self._token(offset, [TokenType.COLON])
        variant_name, offset = self._parse_identifier(offset)

        token = self._peek_token(offset)

        if not token:
            raise EndOfFileException(self.file)

        variables: List[Identifier] = []

        if token.type == TokenType.AS:
            _, offset = self._token(offset, [TokenType.AS])

            variables, offset = self._parse_variables(offset)

        case_label = CaseLabel(enum_name.position, enum_name, variant_name, variables)
        self._print_parse_tree_node("CaseLabel", start_offset, offset)
        return case_label, offset

    def _parse_branch(self, offset: int) -> Tuple[Branch, int]:
        start_offset = offset

        if_token, offset = self._token(offset, [TokenType.IF])
        condition, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.BLOCK_START])
        if_body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.BLOCK_END])

        token = self._peek_token(offset)
        else_body: Optional[FunctionBody] = None

        if token and token.type == TokenType.ELSE:
            _, offset = self._token(offset, [TokenType.ELSE])
            _, offset = self._token(offset, [TokenType.BLOCK_START])
            else_body, offset = self._parse_function_body(offset)
            _, offset = self._token(offset, [TokenType.BLOCK_END])

        branch = Branch(if_token.position, condition, if_body, else_body)

        self._print_parse_tree_node("Branch", start_offset, offset)
        return branch, offset

    def _parse_while_loop(self, offset: int) -> Tuple[WhileLoop, int]:
        start_offset = offset

        while_token, offset = self._token(offset, [TokenType.WHILE])
        condition, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.BLOCK_START])
        body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.BLOCK_END])

        while_loop = WhileLoop(while_token.position, condition, body)
        self._print_parse_tree_node("WhileLoop", start_offset, offset)
        return while_loop, offset

    def _parse_struct_field_query(self, offset: int) -> Tuple[StructFieldQuery, int]:
        start_offset = offset

        field_name, offset = self._parse_string(offset)
        operator_token, offset = self._token(offset, [TokenType.GET_FIELD])

        field_query = StructFieldQuery(
            field_name.position, field_name, operator_token.position
        )

        self._print_parse_tree_node("StructFieldQuery", start_offset, offset)
        return field_query, offset

    def _parse_struct_field_update(self, offset: int) -> Tuple[StructFieldUpdate, int]:
        start_offset = offset

        field_name, offset = self._parse_string(offset)
        _, offset = self._token(offset, [TokenType.BLOCK_START])
        new_value_expr, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.BLOCK_END])
        operator_token, offset = self._token(offset, [TokenType.SET_FIELD])

        field_update = StructFieldUpdate(
            field_name.position, field_name, new_value_expr, operator_token.position
        )
        self._print_parse_tree_node("StructFieldUpdate", start_offset, offset)
        return field_update, offset

    def _parse_get_function_pointer(
        self, offset: int
    ) -> Tuple[GetFunctionPointer, int]:
        start_offset = offset

        function_name, offset = self._parse_string(offset)
        _, offset = self._token(offset, [TokenType.FUNCTION])

        get_function_pointer = GetFunctionPointer(function_name.position, function_name)

        self._print_parse_tree_node("GetFunctionPointer", start_offset, offset)
        return get_function_pointer, offset

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
            elif next_token and next_token.type == TokenType.BLOCK_START:
                item, offset = self._parse_struct_field_update(offset)
            elif next_token and next_token.type == TokenType.FUNCTION:
                item, offset = self._parse_get_function_pointer(offset)
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
                item, offset = self._parse_function_call(offset)

        elif token.type == TokenType.IF:
            item, offset = self._parse_branch(offset)
        elif token.type == TokenType.WHILE:
            item, offset = self._parse_while_loop(offset)
        elif token.type == TokenType.FOREACH:
            item, offset = self._parse_foreach_loop(offset)
        elif token.type == TokenType.USE:
            item, offset = self._parse_use_block(offset)
        elif token.type == TokenType.MATCH:
            item, offset = self._parse_match_block(offset)
        elif token.type == TokenType.RETURN:
            item, offset = self._parse_return(offset)
        elif token.type == TokenType.CALL:
            item, offset = self._parse_call(offset)

        else:
            raise ParserException(
                token,
                [
                    TokenType.FALSE,
                    TokenType.FOREACH,
                    TokenType.IDENTIFIER,
                    TokenType.IF,
                    TokenType.INTEGER,
                    TokenType.MATCH,
                    TokenType.RETURN,
                    TokenType.STRING,
                    TokenType.TRUE,
                    TokenType.WHILE,
                    TokenType.USE,
                ],
            )

        self._print_parse_tree_node("FunctionBodyItem", start_offset, offset)
        return item, offset

    def _parse_return(self, offset: int) -> Tuple[Return, int]:
        start_offset = offset

        return_token, offset = self._token(offset, [TokenType.RETURN])

        self._print_parse_tree_node("Return", start_offset, offset)
        return Return(return_token.position), offset

    def _parse_call(self, offset: int) -> Tuple[Call, int]:
        start_offset = offset

        call_token, offset = self._token(offset, [TokenType.CALL])

        self._print_parse_tree_node("Call", start_offset, offset)
        return Call(call_token.position), offset

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
        _, offset = self._token(offset, [TokenType.BLOCK_START])
        body, offset = self._parse_function_body(offset)
        end_token, offset = self._token(offset, [TokenType.BLOCK_END])

        function.body = body
        function.end_position = end_token.position
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
        enums: List[Enum] = []

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
            elif token.type == TokenType.ENUM:
                enum, offset = self._parse_enum_definition(offset)
                enums.append(enum)
            else:
                break

        parsed_file = ParsedFile(
            position=position,
            functions=functions,
            imports=imports,
            structs=structs,
            enums=enums,
            types=[],
        )

        self._print_parse_tree_node("ParsedFileRoot", start_offset, offset)
        return parsed_file, offset

    def _parse_foreach_loop(self, offset: int) -> Tuple[ForeachLoop, int]:
        start_offset = offset

        foreach_token, offset = self._token(offset, [TokenType.FOREACH])
        _, offset = self._token(offset, [TokenType.BLOCK_START])
        body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.BLOCK_END])

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
        _, offset = self._token(offset, [TokenType.BLOCK_START])
        body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.BLOCK_END])

        use_block = UseBlock(use_token.position, variables, body)
        self._print_parse_tree_node("UseBlock", start_offset, offset)
        return use_block, offset

    def _parse_assignment(self, offset: int) -> Tuple[Assignment, int]:
        start_offset = offset

        variables, offset = self._parse_variables(offset)
        _, offset = self._token(offset, [TokenType.ASSIGN])
        _, offset = self._token(offset, [TokenType.BLOCK_START])
        body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.BLOCK_END])

        assignment = Assignment(variables[0].position, variables, body)
        self._print_parse_tree_node("Assignment", start_offset, offset)
        return assignment, offset

    def _parse_case_block(self, offset: int) -> Tuple[CaseBlock, int]:
        start_offset = offset

        case_token, offset = self._token(offset, [TokenType.CASE])
        label, offset = self._parse_case_label(offset)
        _, offset = self._token(offset, [TokenType.BLOCK_START])
        body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.BLOCK_END])

        case_block = CaseBlock(case_token.position, label, body)
        self._print_parse_tree_node("CaseBlock", start_offset, offset)
        return case_block, offset

    def _parse_default_block(self, offset: int) -> Tuple[DefaultBlock, int]:
        start_offset = offset

        default_token, offset = self._token(offset, [TokenType.DEFAULT])
        _, offset = self._token(offset, [TokenType.BLOCK_START])
        body, offset = self._parse_function_body(offset)
        _, offset = self._token(offset, [TokenType.BLOCK_END])

        default_block = DefaultBlock(default_token.position, body)
        self._print_parse_tree_node("DefaultBlock", start_offset, offset)
        return default_block, offset

    def _parse_match_block(self, offset: int) -> Tuple[MatchBlock, int]:
        start_offset = offset

        blocks: List[CaseBlock | DefaultBlock] = []

        match_token, offset = self._token(offset, [TokenType.MATCH])
        _, offset = self._token(offset, [TokenType.BLOCK_START])

        while True:
            token = self._peek_token(offset)

            if not token or token.type == TokenType.BLOCK_END:
                break

            block: CaseBlock | DefaultBlock

            if token.type == TokenType.CASE:
                block, offset = self._parse_case_block(offset)
            elif token.type == TokenType.DEFAULT:
                block, offset = self._parse_default_block(offset)
            else:
                raise ParserException(token, [TokenType.CASE, TokenType.DEFAULT])
            blocks.append(block)

        _, offset = self._token(offset, [TokenType.BLOCK_END])

        match_block = MatchBlock(match_token.position, blocks)
        self._print_parse_tree_node("MatchBlock", start_offset, offset)
        return match_block, offset

    def _parse_enum_variant(self, offset: int) -> Tuple[EnumVariant, int]:
        start_offset = offset

        name, offset = self._parse_identifier(offset)

        token = self._peek_token(offset)
        if not token:
            raise EndOfFileException(self.file)

        if token.type == TokenType.AS:
            _, offset = self._token(offset, [TokenType.AS])
            associated_data, offset = self._parse_enum_variant_associated_data(offset)
        else:
            associated_data = []

        enum_variant = EnumVariant(name.position, name, associated_data)
        self._print_parse_tree_node("EnumVariant", start_offset, offset)
        return enum_variant, offset

    def _parse_enum_variant_associated_data(
        self, offset: int
    ) -> Tuple[List[TypeLiteral | FunctionPointerTypeLiteral], int]:
        start_offset = offset

        token = self._peek_token(offset)

        if not token:
            raise EndOfFileException(self.file)

        associated_data: List[TypeLiteral | FunctionPointerTypeLiteral] = []

        if token.type == TokenType.BLOCK_START:
            _, offset = self._token(offset, [TokenType.BLOCK_START])

            associated_item, offset = self._parse_type_or_function_pointer_literal(
                offset
            )
            associated_data.append(associated_item)

            while True:
                try:
                    _, offset = self._token(offset, [TokenType.COMMA])
                except ParserBaseException:
                    break

                try:
                    associated_item, offset = self._parse_type_literal(offset)
                except ParserBaseException:
                    break
                else:
                    associated_data.append(associated_item)

            _, offset = self._token(offset, [TokenType.BLOCK_END])
        else:
            type_literal, offset = self._parse_type_or_function_pointer_literal(offset)
            associated_data.append(type_literal)

        self._print_parse_tree_node("EnumVariantAssociatedData", start_offset, offset)
        return associated_data, offset

    def _parse_enum_variants(self, offset: int) -> Tuple[List[EnumVariant], int]:
        start_offset = offset

        enum_variants: List[EnumVariant] = []

        enum_variant, offset = self._parse_enum_variant(offset)
        enum_variants.append(enum_variant)

        while True:
            try:
                _, offset = self._token(offset, [TokenType.COMMA])
            except ParserBaseException:
                break

            try:
                enum_variant, offset = self._parse_enum_variant(offset)
            except ParserBaseException:
                break
            else:
                enum_variants.append(enum_variant)

        self._print_parse_tree_node("EnumVariants", start_offset, offset)
        return enum_variants, offset

    def _parse_enum_definition(self, offset: int) -> Tuple[Enum, int]:
        start_offset = offset

        enum_token, offset = self._token(offset, [TokenType.ENUM])
        name, offset = self._parse_identifier(offset)
        enum_token, offset = self._token(offset, [TokenType.BLOCK_START])
        items, offset = self._parse_enum_variants(offset)
        enum_token, offset = self._token(offset, [TokenType.BLOCK_END])

        enum = Enum(enum_token.position, name, items)
        self._print_parse_tree_node("Enum", start_offset, offset)
        return enum, offset

    def _print_parse_tree_node(
        self, kind: str, start_token_offset: int, end_token_offset: int
    ) -> None:  # pragma: nocover
        if not self.verbose:
            return

        tokens = self.tokens[start_token_offset:end_token_offset]
        tokens_joined = " ".join(token.value for token in tokens)
        print(f"parser | {kind:>20} | {tokens_joined}")

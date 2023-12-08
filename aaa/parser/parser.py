from pathlib import Path
from queue import Queue
from typing import Dict, List, Optional, Type

from basil.exceptions import ParseError, TokenizerException
from basil.file_parser import FileParser
from basil.models import Token

from aaa import aaa_project_root, get_stdlib_path
from aaa.parser.exceptions import AaaParserBaseException, FileReadError
from aaa.parser.models import (
    AaaParseModel,
    Argument,
    Arguments,
    Assignment,
    Boolean,
    Branch,
    Call,
    CaseBlock,
    CaseLabel,
    Char,
    CommaSeparatedTypeList,
    DefaultBlock,
    Enum,
    EnumDeclaration,
    EnumVariant,
    EnumVariantAssociatedData,
    EnumVariants,
    FlatTypeLiteral,
    FlatTypeParams,
    ForeachLoop,
    FreeFunctionCall,
    FreeFunctionName,
    Function,
    FunctionBody,
    FunctionBodyBlock,
    FunctionBodyItem,
    FunctionCall,
    FunctionDeclaration,
    FunctionName,
    FunctionPointerTypeLiteral,
    GetFunctionPointer,
    Identifier,
    Import,
    ImportItem,
    ImportItems,
    Integer,
    MatchBlock,
    MemberFunctionCall,
    MemberFunctionName,
    ParserOutput,
    Return,
    ReturnTypes,
    SourceFile,
    String,
    Struct,
    StructDeclaration,
    StructField,
    StructFieldQuery,
    StructFields,
    StructFieldUpdate,
    TypeLiteral,
    TypeOrFunctionPointerLiteral,
    TypeParams,
    UseBlock,
    Variables,
    WhileLoop,
)
from aaa.runner.exceptions import AaaTranslationException

SYNTAX_JSON_PATH = aaa_project_root() / "syntax.json"

NODE_TYPE_TO_MODEL: Dict[str, Type[AaaParseModel]] = {
    "ARGUMENT": Argument,
    "ARGUMENTS": Arguments,
    "ASSIGNMENT": Assignment,
    "BOOLEAN": Boolean,
    "BRANCH": Branch,
    "CASE_BLOCK": CaseBlock,
    "CASE_LABEL": CaseLabel,
    "COMMA_SEPARATED_TYPE_LIST": CommaSeparatedTypeList,
    "DEFAULT_BLOCK": DefaultBlock,
    "ENUM_DECLARATION": EnumDeclaration,
    "ENUM_DEFINITION": Enum,
    "ENUM_VARIANT_ASSOCIATED_DATA": EnumVariantAssociatedData,
    "ENUM_VARIANT": EnumVariant,
    "ENUM_VARIANTS": EnumVariants,
    "FLAT_TYPE_LITERAL": FlatTypeLiteral,
    "FLAT_TYPE_PARAMS": FlatTypeParams,
    "FOREACH_LOOP": ForeachLoop,
    "FREE_FUNCTION_CALL": FreeFunctionCall,
    "FREE_FUNCTION_NAME": FreeFunctionName,
    "FUNCTION_BODY_BLOCK": FunctionBodyBlock,
    "FUNCTION_BODY_ITEM": FunctionBodyItem,
    "FUNCTION_BODY": FunctionBody,
    "FUNCTION_CALL": FunctionCall,
    "FUNCTION_DECLARATION": FunctionDeclaration,
    "FUNCTION_DEFINITION": Function,
    "FUNCTION_NAME": FunctionName,
    "FUNCTION_POINTER_TYPE_LITERAL": FunctionPointerTypeLiteral,
    "GET_FUNCTION_POINTER": GetFunctionPointer,
    "IMPORT_ITEM": ImportItem,
    "IMPORT_ITEMS": ImportItems,
    "IMPORT": Import,
    "IMPORT": Import,
    "MATCH_BLOCK": MatchBlock,
    "MEMBER_FUNCTION_CALL": MemberFunctionCall,
    "MEMBER_FUNCTION_NAME": MemberFunctionName,
    "RETURN_TYPES": ReturnTypes,
    "SOURCE_FILE": SourceFile,
    "STRUCT_DECLARATION": StructDeclaration,
    "STRUCT_DEFINITION": Struct,
    "STRUCT_FIELD_QUERY": StructFieldQuery,
    "STRUCT_FIELD_UPDATE": StructFieldUpdate,
    "STRUCT_FIELD": StructField,
    "STRUCT_FIELDS": StructFields,
    "TYPE_LITERAL": TypeLiteral,
    "TYPE_OR_FUNCTION_POINTER_LITERAL": TypeOrFunctionPointerLiteral,
    "TYPE_PARAMS": TypeParams,
    "USE_BLOCK": UseBlock,
    "VARIABLES": Variables,
    "WHILE_LOOP": WhileLoop,
}

UNTRANSFORMED_TOKEN_TYPES = {
    "args",
    "as",
    "assign",
    "builtin",
    "case",
    "colon",
    "comma",
    "const",
    "default",
    "else",
    "end",
    "enum",
    "false",
    "fn",
    "foreach",
    "from",
    "get_field",
    "if",
    "import",
    "match",
    "never",
    "set_field",
    "sq_end",
    "sq_start",
    "start",
    "struct",
    "true",
    "use",
    "while",
}

aaa_file_parser = FileParser(SYNTAX_JSON_PATH)


def transform_token(token: Token) -> AaaParseModel | Token:
    if token.type in UNTRANSFORMED_TOKEN_TYPES:
        return token

    if token.type == "identifier":
        return Identifier(token.position, token.value)

    if token.type == "string":
        return String(token.position, unescape_string(token.value[1:-1]))

    if token.type == "char":
        return Char(token.position, unescape_string(token.value[1:-1]))

    if token.type == "integer":
        return Integer(token.position, int(token.value))

    if token.type == "return":
        return Return(token.position)

    if token.type == "call":
        return Call(token.position)

    raise NotImplementedError(f"for {token.type}")


def transform_node(
    node_type: str, children: List[AaaParseModel | Token]
) -> AaaParseModel:
    return NODE_TYPE_TO_MODEL[node_type].load(children)


def unescape_string(escaped: str) -> str:
    simple_escape_sequences = {
        '"': '"',
        "'": "'",
        "/": "/",
        "\\": "\\",
        "0": "\0",
        "b": "\b",
        "e": "\x1b",
        "f": "\f",
        "n": "\n",
        "r": "\r",
        "t": "\t",
    }

    unescaped = ""
    offset = 0

    while offset < len(escaped):
        backslash_offset = escaped.find("\\", offset)

        if backslash_offset == -1:
            unescaped += escaped[offset:]
            break

        unescaped += escaped[offset:backslash_offset]

        escape_determinant = escaped[backslash_offset + 1]

        if escape_determinant in simple_escape_sequences:
            unescaped += simple_escape_sequences[escape_determinant]
            offset = backslash_offset + 2
            continue

        if escape_determinant == "u":
            unicode_hex = escaped[backslash_offset + 2 : backslash_offset + 6]
            unicode_char = chr(int(unicode_hex, 16))
            unescaped += unicode_char
            offset = backslash_offset + 6
            continue

        if escape_determinant == "U":
            unicode_hex = escaped[backslash_offset + 2 : backslash_offset + 10]
            unicode_char = chr(int(unicode_hex, 16))
            unescaped += unicode_char
            offset = backslash_offset + 10
            continue

        # Unknown escape sequence
        raise NotImplementedError

    return unescaped


class AaaParser:
    def __init__(self, verbose: bool) -> None:
        self.verbose = verbose

        self.file_parser = aaa_file_parser
        self.builtins_path = get_stdlib_path() / "builtins.aaa"

        self.exceptions: List[AaaParserBaseException] = []
        self.parsed: Dict[Path, SourceFile] = {}

    def run(self, entrypoint: Path, file_dict: Dict[Path, str]) -> ParserOutput:
        queue: Queue[Path] = Queue()
        queue.put(self.builtins_path)
        queue.put(entrypoint)

        while not queue.empty():
            file = queue.get()

            try:
                source_file: AaaParseModel = self.parse_file(file, file_dict)
                assert isinstance(source_file, SourceFile)

            except (TokenizerException, ParseError) as e:
                self.exceptions.append(AaaParserBaseException(e))
                continue

            except AaaParserBaseException as e:
                self.exceptions.append(e)
                continue

            self.parsed[file] = source_file

            for dependency in source_file.get_dependencies():
                if dependency not in self.parsed:
                    queue.put(dependency)

        if self.exceptions:
            raise AaaTranslationException(self.exceptions)

        return ParserOutput(
            parsed=self.parsed,
            builtins_path=self.builtins_path,
            entrypoint=entrypoint,
        )

    def parse_file(
        self, file: Path, file_dict: Optional[Dict[Path, str]] = None
    ) -> SourceFile:
        file_dict = file_dict or {}

        if file in file_dict:
            text = file_dict[file]
        else:
            try:
                text = file.read_text()
            except OSError:
                raise FileReadError(file)

        model = self.parse_text(text, self.file_parser.root_node_type, str(file))

        assert isinstance(model, SourceFile)
        return model

    def parse_text(
        self, text: str, root_node_type: str, file_name: Optional[str] = None
    ) -> AaaParseModel:
        return self.file_parser.parse_text_and_transform(
            text,
            file_name,
            node_type=root_node_type,
            verbose=self.verbose,
            token_transformer=transform_token,
            node_transformer=transform_node,
        )

    def tokenize_text(self, text: str) -> List[Token]:
        # This is only supposed to be used for testing.
        return self.file_parser.tokenize_text(text, filter_token_types=False)

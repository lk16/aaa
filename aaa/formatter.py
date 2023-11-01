import sys
from bisect import bisect_left
from difflib import unified_diff
from enum import IntEnum, auto
from functools import cached_property
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple, Type

from aaa import Position, get_stdlib_path
from aaa.parser.exceptions import ParserBaseException
from aaa.parser.models import (
    Assignment,
    BooleanLiteral,
    Branch,
    Call,
    CaseBlock,
    DefaultBlock,
    Enum,
    EnumVariant,
    ForeachLoop,
    Function,
    FunctionBody,
    FunctionBodyItem,
    FunctionCall,
    FunctionPointerTypeLiteral,
    GetFunctionPointer,
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
from aaa.parser.single_file_parser import SingleFileParser
from aaa.tokenizer.exceptions import TokenizerBaseException
from aaa.tokenizer.models import Token, TokenType
from aaa.tokenizer.tokenizer import Tokenizer

MAX_LINE_LENGTH = 88
INDENT = 4 * " "
NONEXISTENT_POSITION = Position(Path("/dev/null"), -1, -1)

COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_BLUE = "\033[34m"
COLOR_RESET = "\033[0m"

DIFF_COLORS = {
    " ": ("", ""),
    "-": (COLOR_RED, COLOR_RESET),
    "+": (COLOR_GREEN, COLOR_RESET),
    "@": (COLOR_BLUE, COLOR_RESET),
}


class EnumFormatterResult(IntEnum):
    NO_CHANGES = auto()
    REFORMATTED = auto()
    NEED_REFORMATTING = auto()
    FORMAT_ERROR = auto()


class OneLinerError(Exception):
    """
    Indicates a one-liner could not be created.
    """


def format_diff(before: str, after: str) -> str:  # pragma: nocover
    diff = unified_diff(before.split("\n"), after.split("\n"))
    output_lines: List[str] = []

    for diff_line in diff:
        prefix, suffix = DIFF_COLORS[diff_line[0]]
        output_lines.append(prefix + diff_line + suffix)

    return "\n".join(output_lines) + "\n"


def format_source_files(
    files: Tuple[str], fix_files: bool, show_diff: bool
) -> int:  # pragma: nocover
    files_by_result: Dict[EnumFormatterResult, Set[Path]] = {
        result: set() for result in EnumFormatterResult
    }

    for file_str in files:
        file = Path(file_str)
        formatter = AaaFormatter(file)
        result = formatter.run(fix_files, show_diff)
        files_by_result[result].add(file)

    reformatted = sorted(files_by_result[EnumFormatterResult.REFORMATTED])
    errored = sorted(files_by_result[EnumFormatterResult.FORMAT_ERROR])
    need_reformatting = sorted(files_by_result[EnumFormatterResult.NEED_REFORMATTING])

    summary = f"{len(files)} file(s) were checked.\n"

    exit_code = 0

    if need_reformatting:
        print("Incorrectly formatted:")
        for file in need_reformatting:
            print(file)
        summary += f"{len(need_reformatting)} file(s) need to be reformatted.\n"
        exit_code = 1

    if reformatted:
        print("Reformatting:")
        for file in reformatted:
            print(file)
        summary += f"{len(reformatted)} file(s) were fixed.\n"
        exit_code = 1

    if errored:
        print("Errors while reformatting:")
        for file in errored:
            print(file)
        summary += f"{len(errored)} file(s) had errors.\n"
        exit_code = 2

    print()
    print(summary, end="")
    return exit_code


class AaaFormatter:
    def __init__(self, file: Path) -> None:
        self.file = file
        self.verbose = False
        self.comments: List[Token] = []
        self.whitespace: List[Token] = []
        self.filtered_tokens: List[Token] = []

    @cached_property
    def block_formatters(self) -> Dict[Type[FunctionBodyItem], Callable[..., str]]:
        return {
            Assignment: self._format_assignment,
            Branch: self._format_branch,
            ForeachLoop: self._format_foreach_loop,
            MatchBlock: self._format_match_block,
            WhileLoop: self._format_while_loop,
            UseBlock: self._format_use_block,
        }

    @cached_property
    def non_block_formatters(self) -> Dict[Type[FunctionBodyItem], Callable[..., str]]:
        return {
            BooleanLiteral: self._format_boolean_literal,
            Call: self._format_call,
            FunctionCall: self._format_function_call,
            FunctionPointerTypeLiteral: self._format_function_pointer_type_literal,
            GetFunctionPointer: self._format_get_function_pointer,
            IntegerLiteral: self._format_integer_literal,
            Return: self._format_return,
            StringLiteral: self._format_string_literal,
            StructFieldQuery: self._format_struct_field_query,
            StructFieldUpdate: self._format_struct_field_update,
        }

    def run(
        self, fix_file: bool, show_diff: bool
    ) -> EnumFormatterResult:  # pragma: nocover
        before = self.file.read_text()

        try:
            after = self.get_formatted()
        except TokenizerBaseException as e:
            print(str(e), file=sys.stderr)
            return EnumFormatterResult.FORMAT_ERROR
        except ParserBaseException as e:
            print(str(e), file=sys.stderr)
            return EnumFormatterResult.FORMAT_ERROR

        if show_diff:
            diff = format_diff(before, after)

            if diff != "\n":
                print(diff)

        if before != after and fix_file:
            self.file.write_text(after)

        if before != after:
            if fix_file:
                return EnumFormatterResult.REFORMATTED
            return EnumFormatterResult.NEED_REFORMATTING

        return EnumFormatterResult.NO_CHANGES

    def get_formatted(self, *, force_parse_as_builtins_file: bool = False) -> str:
        tokenizer = Tokenizer(self.file, self.verbose)

        tokens = tokenizer.tokenize_unfiltered()

        self.comments = [token for token in tokens if token.type == TokenType.COMMENT]

        self.whitespace = [
            token for token in tokens if token.type == TokenType.WHITESPACE
        ]

        self.filtered_tokens = [
            token
            for token in tokens
            if token.type not in [TokenType.COMMENT, TokenType.WHITESPACE]
        ]

        parser = SingleFileParser(self.file, self.filtered_tokens, self.verbose)

        if self.file.resolve() == get_stdlib_path() or force_parse_as_builtins_file:
            parsed_file = parser.parse_builtins_file()
        else:
            parsed_file = parser.parse_regular_file()

        # TODO re-add comments

        return self._format_parsed_file(parsed_file)

    def _format_parsed_file(self, parsed_file: ParsedFile) -> str:
        formatted_sections: List[str] = []

        formatted_imports = self._format_imports(parsed_file.imports)
        if formatted_imports:
            formatted_sections.append(formatted_imports)

        top_level_items: List[Function | Struct | Enum] = []
        top_level_items += parsed_file.functions
        top_level_items += parsed_file.structs
        top_level_items += parsed_file.enums

        def sort_key(item: Function | Struct | Enum) -> Position:
            return item.position

        for item in sorted(top_level_items, key=sort_key):
            if isinstance(item, Function):
                formatted_sections.append(self._format_function(item))
            elif isinstance(item, Struct):
                formatted_sections.append(self._format_struct_definition(item))
            else:
                assert isinstance(item, Enum)
                formatted_sections.append(self._format_enum_definition(item))

        return "\n".join(formatted_sections)

    def _format_imports(self, imports: List[Import]) -> str:
        imports_by_source: Dict[str, List[Import]] = {}

        for import_ in imports:
            source = import_.source

            if source not in imports_by_source:
                imports_by_source[source] = []

            imports_by_source[source].append(import_)

        merged_imports: List[Import] = []

        for source, imports in imports_by_source.items():
            imported_items: List[ImportItem] = []

            for import_ in imports:
                imported_items += import_.imported_items

            merged_import = Import(NONEXISTENT_POSITION, source, imported_items)
            merged_imports.append(merged_import)

        def sort_key(import_: Import) -> str:
            return import_.source

        formatted_imports: List[str] = []
        for import_ in sorted(merged_imports, key=sort_key):
            formatted_imports.append(self._format_import(import_))

        return "\n".join(formatted_imports)

    def _format_import(self, import_: Import) -> str:
        start = f'from "{import_.source}" import'

        formatted_items: List[str] = []

        def sort_key(item: ImportItem) -> str:
            return item.original.name

        for item in sorted(import_.imported_items, key=sort_key):
            if item.original == item.imported:
                formatted_items.append(item.original.name)
            else:
                formatted_items.append(f"{item.original.name} as {item.imported.name}")

        one_line = start + " " + ", ".join(formatted_items) + "\n"

        if len(one_line) <= MAX_LINE_LENGTH:
            return one_line

        multi_line = start + "\n"
        for formatted_item in formatted_items:
            multi_line += f"{INDENT}{formatted_item},\n"

        return multi_line

    def _format_type_or_function_pointer(
        self, item: TypeLiteral | FunctionPointerTypeLiteral
    ) -> str:
        if isinstance(item, TypeLiteral):
            return self._format_type_literal(item)
        else:
            assert isinstance(item, FunctionPointerTypeLiteral)
            return self._format_function_pointer_type_literal(item, 0)

    def _format_type_literal(self, type_literal: TypeLiteral) -> str:
        code = ""

        if type_literal.const:
            code += "const "

        code += type_literal.identifier.name

        if type_literal.params:
            formatted_params = [
                self._format_type_or_function_pointer(param)
                for param in type_literal.params
            ]

            code += "[" + ", ".join(formatted_params) + "]"

        return code

    def _format_struct_definition(self, struct: Struct) -> str:
        start = f"struct {struct.identifier.name} {{"

        end = "}\n"

        fields = ""

        for field_name, field_type in struct.fields.items():
            type = self._format_type_or_function_pointer(field_type)
            fields += f"{INDENT}{field_name} as {type},\n"

        if not fields:
            return start + end

        return start + "\n" + fields + end

    def _format_enum_variant(self, enum_variant: EnumVariant) -> str:
        prefix = f"{INDENT}{enum_variant.name.name}"

        if not enum_variant.associated_data:
            return prefix + ",\n"

        associated_data: List[str] = [
            self._format_type_or_function_pointer(item)
            for item in enum_variant.associated_data
        ]

        # Special case: remove unnecessary brackets
        if len(enum_variant.associated_data) == 1:
            return prefix + " as " + associated_data[0] + ",\n"

        one_line = prefix + " as { " + ", ".join(associated_data) + " },\n"

        if len(one_line) <= MAX_LINE_LENGTH:
            return one_line

        return (
            prefix
            + " as {\n"
            + "".join(f"{2*INDENT}{item},\n" for item in associated_data)
            + f"{INDENT}}}\n"
        )

    def _format_enum_definition(self, enum: Enum) -> str:
        code = f"enum {enum.identifier.name} {{\n"

        for variant in enum.variants:
            code += self._format_enum_variant(variant)

        code += "}\n"

        return code

    def _format_function_declaration(self, function: Function) -> str:
        prefix = "fn "

        formatted_params = ""
        if function.type_params:
            formatted_params = (
                "["
                + ", ".join(param.identifier.name for param in function.type_params)
                + "]"
            )

        if function.struct_name:
            prefix += f"{function.struct_name.name}{formatted_params}:{function.func_name.name}"

        else:
            prefix += f"{function.func_name.name}{formatted_params}"

        argument_items: List[str] = []
        for argument in function.arguments:
            argument_type = self._format_type_or_function_pointer(argument.type)
            argument_items.append(f"{argument.identifier.name} as {argument_type}")

        if isinstance(function.return_types, Never):
            return_type_items = ["never"]
        else:
            return_type_items = [
                self._format_type_or_function_pointer(return_type)
                for return_type in function.return_types
            ]

        single_line = prefix
        if argument_items:
            single_line += " args " + ", ".join(argument_items)

        if return_type_items:
            single_line += " return " + ", ".join(return_type_items)

        if len(single_line) <= MAX_LINE_LENGTH:
            return single_line

        multi_line_arguments = ""
        multi_line_return_types = ""

        if argument_items:
            multi_line_arguments = f"{INDENT}args " + ", ".join(argument_items) + "\n"

            if len(multi_line_arguments) > MAX_LINE_LENGTH:
                multi_line_arguments = f"{INDENT}args\n"
                for item in argument_items:
                    multi_line_arguments += f"{2*INDENT}{item},\n"

        if return_type_items:
            multi_line_return_types = (
                f"{INDENT}return " + ", ".join(return_type_items) + "\n"
            )

            if len(multi_line_return_types) > MAX_LINE_LENGTH:
                multi_line_return_types = f"{INDENT}return\n"
                for item in return_type_items:
                    multi_line_return_types += f"{2*INDENT}{item},\n"

        multi_line = prefix + "\n" + multi_line_arguments + multi_line_return_types

        if multi_line.endswith("\n"):
            multi_line = multi_line[:-1]

        return multi_line

    def _format_function_body_as_one_liner(self, body: FunctionBody) -> str:
        return self._format_function_body_non_block_items(
            body.items, 0, force_one_liner=True
        )

    def _get_non_block_items_slice_end(self, body: FunctionBody, index: int) -> int:
        while True:
            if index >= len(body.items):
                return index

            if type(body.items[index]) in self.block_formatters:
                return index

            index += 1

    def _format_function_body(self, body: FunctionBody, indent_level: int) -> str:
        index = 0
        code = ""

        while True:
            try:
                item = body.items[index]
            except IndexError:
                break

            if index > 0:
                token = Token(item.position, TokenType.WHITESPACE, "")
                prev_token_index = bisect_left(self.filtered_tokens, token) - 1
                prev_token = self.filtered_tokens[prev_token_index]

                # We keep at most one empty line between items.
                if item.position.line - prev_token.position.line > 1:
                    code += "\n"

            if type(item) in self.block_formatters:
                formatter = self.block_formatters[type(item)]
                code += formatter(item, indent_level)
                index += 1
            else:
                next_block_index = self._get_non_block_items_slice_end(body, index)
                non_block_items = body.items[index:next_block_index]

                formatted_items = self._format_function_body_non_block_items(
                    non_block_items, indent_level
                )
                code += formatted_items
                index = next_block_index

        return code

    def _format_function_body_non_block_items(
        self,
        items: List[FunctionBodyItem],
        indent_level: int,
        *,
        force_one_liner: bool = False,
    ) -> str:
        formatted_items: List[str] = []

        for item in items:
            try:
                formatter = self.non_block_formatters[type(item)]
            except KeyError:
                if not force_one_liner:  # pragma: nocover
                    raise NotImplementedError
                raise OneLinerError

            formatted_items.append(formatter(item, indent_level))

        if force_one_liner:
            return " ".join(formatted_items)

        code = ""
        line = indent_level * INDENT + formatted_items[0]

        for i in range(1, len(formatted_items)):
            formatted_item = formatted_items[i]
            prev_position = items[i - 1].position
            position = items[i].position

            # This works because WHITESPACE is the only Token that can contain newlines
            newlines_count = position.line - prev_position.line

            if newlines_count == 0:
                if len(line + " " + formatted_item + "\n") >= MAX_LINE_LENGTH:
                    code += line + "\n"
                    line = indent_level * INDENT + formatted_item
                else:
                    line += " " + formatted_item
            elif newlines_count == 1:
                code += f"{line}\n"
                line = indent_level * INDENT + formatted_item
            else:
                code += f"{line}\n\n"
                line = indent_level * INDENT + formatted_item

        code += f"{line}\n"
        return code

    def _format_function(self, function: Function) -> str:
        code = self._format_function_declaration(function)

        if not function.body:
            return code + "\n"

        return code + " {\n" + self._format_function_body(function.body, 1) + "}\n"

    def _format_assignment(self, item: Assignment, indent_level: int) -> str:
        prefix = (
            indent_level * INDENT
            + ", ".join(var.name for var in item.variables)
            + " <- {"
        )

        try:
            one_line = (
                prefix
                + " "
                + self._format_function_body_as_one_liner(item.body)
                + " }\n"
            )
        except OneLinerError:
            pass
        else:
            if len(one_line) <= MAX_LINE_LENGTH:
                return one_line

        return (
            prefix
            + "\n"
            + self._format_function_body(item.body, indent_level + 1)
            + indent_level * INDENT
            + "}\n"
        )

    def _format_boolean_literal(self, item: BooleanLiteral, indent_level: int) -> str:
        return str(item.value).lower()

    def _format_branch(self, item: Branch, indent_level: int) -> str:
        formatted_condition = self._format_function_body(
            item.condition, indent_level + 1
        )

        one_line_if: Optional[str] = None

        if formatted_condition.strip().count("\n") == 0:
            one_line_if = (
                indent_level * INDENT + "if " + formatted_condition.strip() + " {\n"
            )

        if one_line_if is not None and len(one_line_if) <= MAX_LINE_LENGTH:
            formatted_if = one_line_if
        else:
            formatted_if = (
                indent_level * INDENT
                + "if\n"
                + self._format_function_body(item.condition, indent_level + 1)
                + indent_level * INDENT
                + "{\n"
            )

        code = formatted_if + self._format_function_body(item.if_body, indent_level + 1)

        if item.else_body:
            code += (
                indent_level * INDENT
                + "} else {\n"
                + self._format_function_body(item.else_body, indent_level + 1)
            )

        code += indent_level * INDENT + "}\n"

        return code

    def _format_call(self, item: Call, indent_level: int) -> str:
        return "call"

    def _format_foreach_loop(self, item: ForeachLoop, indent_level: int) -> str:
        return (
            indent_level * INDENT
            + "foreach {\n"
            + self._format_function_body(item.body, indent_level + 1)
            + indent_level * INDENT
            + "}\n"
        )

    def _format_function_call(self, item: FunctionCall, indent_level: int) -> str:
        formatted_params = ""
        if item.type_params:
            formatted_params = (
                "["
                + ", ".join(
                    self._format_type_or_function_pointer(param)
                    for param in item.type_params
                )
                + "]"
            )

        return f"{item.name()}{formatted_params}"

    def _format_function_pointer_type_literal(
        self,
        func_ptr_literal: FunctionPointerTypeLiteral,
        indent_level: int,
    ) -> str:
        formatted_arguments = [
            self._format_type_or_function_pointer(arg)
            for arg in func_ptr_literal.argument_types
        ]

        if isinstance(func_ptr_literal.return_types, Never):
            formatted_return_types = ["never"]
        else:
            formatted_return_types = [
                self._format_type_or_function_pointer(return_type)
                for return_type in func_ptr_literal.return_types
            ]

        return (
            "fn["
            + ", ".join(formatted_arguments)
            + "]["
            + ", ".join(formatted_return_types)
            + "]"
        )

    def _format_get_function_pointer(
        self, item: GetFunctionPointer, indent_level: int
    ) -> str:
        return item.function_name.as_aaa_literal() + " fn"

    def _format_integer_literal(self, item: IntegerLiteral, indent_level: int) -> str:
        return str(item.value)

    def _format_match_case_block(self, item: CaseBlock, indent_level: int) -> str:
        prefix = (
            indent_level * INDENT
            + f"case {item.label.enum_name.name}:{item.label.variant_name.name}"
        )

        if item.label.variables:
            prefix += " as " + ", ".join(var.name for var in item.label.variables)

        prefix += " {"

        try:
            one_line = (
                f"{prefix} "
                + self._format_function_body_as_one_liner(item.body)
                + " }\n"
            )
        except OneLinerError:
            pass
        else:
            if len(one_line) <= MAX_LINE_LENGTH:
                return one_line

        return (
            f"{prefix}\n"
            + self._format_function_body(item.body, indent_level + 1)
            + indent_level * INDENT
            + "}\n"
        )

    def _format_match_default_block(self, item: DefaultBlock, indent_level: int) -> str:
        prefix = indent_level * INDENT + "default {"

        try:
            one_line = (
                f"{prefix} "
                + self._format_function_body_as_one_liner(item.body)
                + " }\n"
            )
        except OneLinerError:
            pass
        else:
            if len(one_line) <= MAX_LINE_LENGTH:
                return one_line

        return (
            f"{prefix}\n"
            + self._format_function_body(item.body, indent_level + 1)
            + indent_level * INDENT
            + "}\n"
        )

    def _format_match_block(self, item: MatchBlock, indent_level: int) -> str:
        code = indent_level * INDENT + "match {\n"

        for block in item.blocks:
            if isinstance(block, CaseBlock):
                code += self._format_match_case_block(block, indent_level + 1)
            else:
                assert isinstance(block, DefaultBlock)
                code += self._format_match_default_block(block, indent_level + 1)

        code += indent_level * INDENT + "}\n"
        return code

    def _format_return(self, item: Return, indent_level: int) -> str:
        return "return"

    def _format_string_literal(self, item: StringLiteral, indent_level: int) -> str:
        return item.as_aaa_literal()

    def _format_struct_field_query(
        self, item: StructFieldQuery, indent_level: int
    ) -> str:
        return item.field_name.as_aaa_literal() + " ?"

    def _format_struct_field_update(
        self, item: StructFieldUpdate, indent_level: int
    ) -> str:
        try:
            one_line = (
                item.field_name.as_aaa_literal()
                + " { "
                + self._format_function_body_as_one_liner(item.new_value_expr)
                + " } !"
            )
        except OneLinerError:
            pass
        else:
            if len(one_line) <= MAX_LINE_LENGTH:
                return one_line

        return (
            item.field_name.as_aaa_literal()
            + " {\n"
            + self._format_function_body(item.new_value_expr, indent_level + 1)
            + indent_level * INDENT
            + "} !"
        )

    def _format_use_block(self, item: UseBlock, indent_level: int) -> str:
        prefix_line = (
            indent_level * INDENT
            + "use "
            + ", ".join(var.name for var in item.variables)
            + " {\n"
        )

        if len(prefix_line) >= MAX_LINE_LENGTH:
            var_indent = (indent_level + 1) * INDENT
            prefix_line = (
                indent_level * INDENT
                + "use\n"
                + "".join(f"{var_indent}{var.name},\n" for var in item.variables)
                + indent_level * INDENT
                + "{\n"
            )

        return (
            prefix_line
            + self._format_function_body(item.body, indent_level + 1)
            + indent_level * INDENT
            + "}\n"
        )

    def _format_while_loop(self, item: WhileLoop, indent_level: int) -> str:
        suffix = (
            self._format_function_body(item.body, indent_level + 1)
            + indent_level * INDENT
            + "}\n"
        )

        try:
            condition_one_line = (
                indent_level * INDENT
                + "while "
                + self._format_function_body_as_one_liner(item.condition)
                + " {\n"
            )
        except OneLinerError:
            pass
        else:
            if len(condition_one_line) <= MAX_LINE_LENGTH:
                return condition_one_line + suffix

        return (
            indent_level * INDENT
            + "while\n"
            + self._format_function_body(item.condition, indent_level + 1)
            + indent_level * INDENT
            + "{\n"
            + suffix
        )

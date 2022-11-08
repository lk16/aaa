import subprocess
import sys
from hashlib import sha256
from pathlib import Path

from aaa.cross_referencer.models import (
    BooleanLiteral,
    Branch,
    CrossReferencerOutput,
    Function,
    FunctionBody,
    FunctionBodyItem,
    Identifier,
    IdentifierCallingFunction,
    IdentifierCallingType,
    IdentifierUsingArgument,
    IntegerLiteral,
    Loop,
    StringLiteral,
    StructFieldQuery,
    StructFieldUpdate,
    Unresolved,
)

AAA_C_BUILTIN_FUNCS = {
    "-": "aaa_stack_minus",
    "!=": "aaa_stack_unequal",
    ".": "aaa_stack_print",
    "*": "aaa_stack_multiply",
    "/": "aaa_stack_divide",
    "%": "aaa_stack_modulo",
    "+": "aaa_stack_plus",
    "<": "aaa_stack_less",
    "<=": "aaa_stack_less_equal",
    "=": "aaa_stack_equals",
    ">": "aaa_stack_greater",
    ">=": "aaa_stack_greater_equal",
    "accept": "aaa_stack_accept",
    "and": "aaa_stack_and",
    "assert": "aaa_stack_assert",
    "bind": "aaa_stack_bind",
    "connect": "aaa_stack_connect",
    "drop": "aaa_stack_drop",
    "dup": "aaa_stack_dup",
    "exit": "aaa_stack_exit",
    "listen": "aaa_stack_listen",
    "map:clear": "aaa_stack_map_clear",
    "map:drop": "aaa_stack_map_drop",
    "map:empty": "aaa_stack_map_empty",
    "map:get": "aaa_stack_map_get",
    "map:has_key": "aaa_stack_map_has_key",
    "map:pop": "aaa_stack_map_pop",
    "map:set": "aaa_stack_map_set",
    "map:size": "aaa_stack_map_size",
    "nop": "aaa_stack_nop",
    "not": "aaa_stack_not",
    "or": "aaa_stack_or",
    "over": "aaa_stack_over",
    "read": "aaa_stack_read",
    "repr": "aaa_stack_repr",
    "rot": "aaa_stack_rot",
    "socket": "aaa_stack_socket",
    "str:equals": "aaa_stack_str_equals",
    "swap": "aaa_stack_swap",
    "vec:clear": "aaa_stack_vec_clear",
    "vec:empty": "aaa_stack_vec_empty",
    "vec:get": "aaa_stack_vec_get",
    "vec:pop": "aaa_stack_vec_pop",
    "vec:push": "aaa_stack_vec_push",
    "vec:set": "aaa_stack_vec_set",
    "vec:size": "aaa_stack_vec_size",
    "write": "aaa_stack_write",
}

C_IDENTATION = " " * 4


class Transpiler:
    def __init__(
        self, cross_referencer_output: CrossReferencerOutput, output_file: Path
    ) -> None:
        self.output_file = output_file
        self.types = cross_referencer_output.types
        self.functions = cross_referencer_output.functions
        self.builtins_path = cross_referencer_output.builtins_path
        self.entrypoint = cross_referencer_output.entrypoint

    def run(self, compile: bool, run_binary: bool) -> int:
        code = self._generate_c_file()
        self.output_file.write_text(code)

        if run_binary and not compile:
            print("Can't run binary without (re-)compiling!", file=sys.stderr)
            return 1

        if compile:
            exit_code = subprocess.run(
                [
                    "gcc",
                    "-Wall",
                    "-Wextra",
                    # "--coverage", TODO enable this flag with flag
                    "-I",
                    "./aaa/transpiler/",
                    "-o",
                    "generated",
                    "-std=gnu99",
                    "-g",
                    str(self.output_file),
                    "aaa/transpiler/aaa.c",
                ]
            ).returncode

            if exit_code != 0:
                return exit_code

        if run_binary:
            return subprocess.run(["./generated"]).returncode

        return 0

    def _indent(self, indent: int) -> str:
        return C_IDENTATION * indent

    def _generate_c_file(self) -> str:
        includes = '#include "aaa.h"\n'

        # TODO generate forward declaration of types

        # TODO generate type definitions

        forward_func_declarations = ""

        for function in self.functions.values():
            if function.file == self.builtins_path:
                continue
            func_name = self._generate_c_function_name(function)
            forward_func_declarations += f"void {func_name}(struct aaa_stack *stack);\n"

        content = ""

        for function in self.functions.values():
            if function.file == self.builtins_path:
                continue
            content += self._generate_c_function(function)
            content += "\n"

        aaa_user_main_func = self.functions[(self.entrypoint, "main")]
        aaa_user_main_name = self._generate_c_function_name(aaa_user_main_func)

        content += "int main(int argc, char **argv) {\n"
        content += "    (void)argc;\n"
        content += "    (void)argv;\n"
        content += "    struct aaa_stack stack;\n"
        content += "    aaa_stack_init(&stack);\n"
        content += f"    {aaa_user_main_name}(&stack);\n"
        content += "    aaa_stack_free(&stack);\n"
        content += "    return 0;\n"
        content += "}\n"

        return includes + "\n" + forward_func_declarations + "\n" + content

    def _generate_c_function_name(self, function: Function) -> str:
        # hash file and name to prevent naming collisions
        hash_input = f"{function.file} {function.name}"
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]
        return f"aaa_user_{hash}"

    def _generate_c_function(self, function: Function) -> str:
        assert not isinstance(function.body, Unresolved)
        assert not isinstance(function.arguments, Unresolved)

        indentation = "    "

        if not function.body:
            # TODO better handling
            raise ValueError(f"No body for function {function.identify()}")

        func_name = self._generate_c_function_name(function)

        content = f"// Generated from: {function.file} {function.name}\n"
        content += f"void {func_name}(struct aaa_stack *stack) {{\n"

        if function.arguments:
            content += f"{indentation}// load arguments\n"
            for arg in reversed(function.arguments):
                content += f"{indentation}struct aaa_variable {arg.name} = *aaa_stack_pop(stack);\n"
            content += "\n"

        content += self._generate_c_function_body(function.body, 1)
        content += "}\n"

        return content

    def _generate_c_function_body(
        self, function_body: FunctionBody, indent: int
    ) -> str:
        code = ""

        for item in function_body.items:
            code += self._generate_c_function_body_item(item, indent)

        return code

    def _generate_c_function_body_item(
        self, item: FunctionBodyItem, indent: int
    ) -> str:
        indentation = self._indent(indent)

        if isinstance(item, FunctionBody):
            return self._generate_c_function_body(item, indent)
        elif isinstance(item, IntegerLiteral):
            return f"{indentation}aaa_stack_push_int(stack, {item.value});\n"
        elif isinstance(item, StringLiteral):
            # TODO this is horrible
            string_value = '"' + repr(item.value)[1:-1].replace('"', '\\"') + '"'
            return f"{indentation}aaa_stack_push_str(stack, {string_value});\n"
        elif isinstance(item, BooleanLiteral):
            bool_value = "true"
            if not item.value:
                bool_value = "false"
            return f"{indentation}aaa_stack_push_bool(stack, {bool_value});\n"
        elif isinstance(item, Loop):
            return self._generate_c_loop(item, indent)
        elif isinstance(item, Identifier):
            return self._generate_c_identifier_code(item, indent)
        elif isinstance(item, Branch):
            return self._generate_c_branch(item, indent)
        elif isinstance(item, StructFieldQuery):
            # TODO
            return self._generate_c_not_implemented("StructFieldQuery", indent)
        elif isinstance(item, StructFieldUpdate):
            # TODO
            return self._generate_c_not_implemented("StructFieldUpdate", indent)
        else:  # pragma: nocover
            assert False

    def _generate_c_loop(self, loop: Loop, indent: int) -> str:
        condition_code = self._generate_c_function_body(loop.condition, indent + 1)
        body_code = self._generate_c_function_body(loop.body, indent + 1)

        return (
            f"{self._indent(indent)}while (true) {{\n"
            + condition_code
            + f"{self._indent(indent+1)}if (!aaa_stack_pop_bool(stack)) {{\n"
            + f"{self._indent(indent+2)}break;\n"
            + f"{self._indent(indent+1)}}}\n"
            + body_code
            + f"{self._indent(indent)}}}\n"
        )

    def _generate_c_identifier_code(self, identifier: Identifier, indent: int) -> str:
        indentation = self._indent(indent)

        if isinstance(identifier.kind, IdentifierCallingFunction):
            called = identifier.kind.function
            c_func_name = ""

            if called.file == self.builtins_path:
                try:
                    c_func_name = AAA_C_BUILTIN_FUNCS[called.name]
                except KeyError:
                    # TODO
                    return self._generate_c_not_implemented(identifier.name, indent)

            else:
                c_func_name = self._generate_c_function_name(called)

            return f"{indentation}{c_func_name}(stack);\n"

        if isinstance(identifier.kind, IdentifierUsingArgument):
            return f"{indentation}aaa_stack_push_variable(stack, &{identifier.name});\n"

        if isinstance(identifier.kind, IdentifierCallingType):
            var_type = identifier.kind.var_type

            if var_type.type.file == self.builtins_path:
                if var_type.name == "int":
                    return f"{indentation}aaa_stack_push_int(stack, 0);\n"
                elif var_type.name == "str":
                    return f'{indentation}aaa_stack_push_str(stack, "");\n'
                elif var_type.name == "bool":
                    return f"{indentation}aaa_stack_push_bool(stack, false);\n"
                elif var_type.name == "vec":
                    return f"{indentation}aaa_stack_push_vec(stack);\n"
                elif var_type.name == "map":
                    return f"{indentation}aaa_stack_push_map(stack);\n"
                else:  # pragma: nocover
                    assert False

            # TODO
            return self._generate_c_not_implemented("IdentifierCallingType", indent)

        assert False

    def _generate_c_branch(self, branch: Branch, indent: int) -> str:
        indentation = self._indent(indent)

        condition_code = self._generate_c_function_body(branch.condition, indent)
        if_code = self._generate_c_function_body(branch.if_body, indent + 1)
        else_code = self._generate_c_function_body(branch.else_body, indent + 1)

        code = (
            condition_code
            + f"{indentation}if (aaa_stack_pop_bool(stack)) {{\n"
            + if_code
        )

        if branch.else_body.items:
            code += f"{indentation}}} else {{\n" + else_code

        code += f"{indentation}}}\n"

        return code

    def _generate_c_not_implemented(self, unimplemented: str, indent: int) -> str:
        indentation = self._indent(indent)

        return f'{indentation}aaa_stack_not_implemented(stack, "{unimplemented}");\n'

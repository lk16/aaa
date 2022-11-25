import subprocess
import sys
from glob import glob
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
    Type,
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
            c_files = [str(self.output_file)] + glob("./c/*.c")

            exit_code = subprocess.run(
                [
                    "gcc",
                    "-Wall",
                    "-Wextra",
                    # "--coverage", TODO enable this flag with flag
                    "-I",
                    "./c/",
                    "-o",
                    "generated",
                    "-std=gnu99",
                    "-g",
                    "-Werror",
                ]
                + c_files
            ).returncode

            if exit_code != 0:
                return exit_code

        if run_binary:
            return subprocess.run(["./generated"]).returncode

        return 0

    def _indent(self, indent: int) -> str:
        return C_IDENTATION * indent

    def _generate_c_file(self) -> str:
        content = '#include "aaa.h"\n'
        content += "\n"

        for type in self.types.values():
            content += self._generate_c_struct_new_func(type)

        # TODO struct member functions

        for function in self.functions.values():
            if function.file == self.builtins_path:
                continue
            func_name = self._generate_c_function_name(function)
            content += f"void {func_name}(struct aaa_stack *stack);\n"

        content += "\n"

        for function in self.functions.values():
            if function.file == self.builtins_path:
                continue
            content += self._generate_c_function(function)

        content += self._generate_c_main_function()

        return content

    def _generate_c_main_function(self) -> str:
        aaa_user_main_func = self.functions[(self.entrypoint, "main")]
        aaa_user_main_name = self._generate_c_function_name(aaa_user_main_func)

        return (
            "int main(int argc, char **argv) {\n"
            + "    (void)argc;\n"
            + "    (void)argv;\n"
            + "    struct aaa_stack stack;\n"
            + "    aaa_stack_init(&stack);\n"
            + f"    {aaa_user_main_name}(&stack);\n"
            + "    aaa_stack_free(&stack);\n"
            + "    return 0;\n"
            + "}\n"
        )

    def _generate_c_builtin_function_name(self, function: Function) -> str:
        if function.name in AAA_C_BUILTIN_FUNCS:
            return AAA_C_BUILTIN_FUNCS[function.name]

        return "aaa_stack_" + function.name.replace(":", "_")

    def _generate_c_function_name(self, function: Function) -> str:
        if function.file == self.builtins_path:
            return self._generate_c_builtin_function_name(function)

        # hash file and name to prevent naming collisions
        hash_input = f"{function.file} {function.name}"
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]
        return f"aaa_user_func_{hash}"

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
        content += "}\n\n"

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
            return (
                f"{indentation}aaa_stack_push_str_raw(stack, {string_value}, false);\n"
            )
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
            return (
                f'{indentation}aaa_stack_push_str_raw(stack, "{item.field_name.value}", false);\n'
                + f"{indentation}aaa_stack_field_query(stack);\n"
            )
        elif isinstance(item, StructFieldUpdate):
            return (
                f'{indentation}aaa_stack_push_str_raw(stack, "{item.field_name.value}", false);\n'
                + self._generate_c_function_body(item.new_value_expr, indent)
                + f"{indentation}aaa_stack_field_update(stack);\n"
            )
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
            c_func_name = self._generate_c_function_name(identifier.kind.function)
            return f"{indentation}{c_func_name}(stack);\n"

        if isinstance(identifier.kind, IdentifierUsingArgument):
            return f"{indentation}aaa_stack_push_variable(stack, &{identifier.name});\n"

        if isinstance(identifier.kind, IdentifierCallingType):
            var_type = identifier.kind.var_type

            if var_type.type.file == self.builtins_path:
                if var_type.name == "int":
                    return f"{indentation}aaa_stack_push_int(stack, 0);\n"
                elif var_type.name == "str":
                    return f'{indentation}aaa_stack_push_str_raw(stack, "", false);\n'
                elif var_type.name == "bool":
                    return f"{indentation}aaa_stack_push_bool(stack, false);\n"
                elif var_type.name == "vec":
                    return f"{indentation}aaa_stack_push_vec_empty(stack);\n"
                elif var_type.name == "map":
                    return f"{indentation}aaa_stack_push_map_empty(stack);\n"
                else:  # pragma: nocover
                    assert False

            c_struct_name = self._generate_c_struct_name(var_type.type)
            return (
                f"{indentation}aaa_stack_push_struct(stack, {c_struct_name}_new());\n"
            )

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

    def _generate_c_struct_name(self, type: Type) -> str:
        hash_input = f"{type.file} {type.name}"
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]
        return f"aaa_user_struct_{hash}"

    def _generate_c_struct_new_func(self, type: Type) -> str:
        assert not isinstance(type.fields, Unresolved)

        if type.file == self.builtins_path and not type.fields:
            return ""

        c_struct_name = self._generate_c_struct_name(type)

        code = f"// Generated for: {type.file} {type.name}\n"
        code += f"struct aaa_struct *{c_struct_name}_new(void) {{\n"
        code += f'{C_IDENTATION}struct aaa_struct *s = aaa_struct_new("{type.name}");\n'

        for field_name, field_type in type.fields.items():
            code += f"{C_IDENTATION}struct aaa_variable *{field_name} = "
            if field_type.name == "int":
                code += "aaa_variable_new_int_zero_value();\n"
            elif field_type.name == "bool":
                code += "aaa_variable_new_bool_zero_value();\n"
            elif field_type.name == "str":
                code += "aaa_variable_new_str_zero_value();\n"
            elif field_type.name == "vec":
                code += "aaa_variable_new_vector_zero_value();\n"
            elif field_type.name == "map":
                code += "aaa_variable_new_map_zero_value();\n"
            else:
                raise NotImplementedError

            code += f'{C_IDENTATION}aaa_struct_create_field(s, "{field_name}", {field_name});\n'
            code += f"{C_IDENTATION}aaa_variable_dec_ref({field_name});\n"

        code += f"{C_IDENTATION}return s;\n"
        code += "}\n\n"

        return code

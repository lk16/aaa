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
    IdentifierUsingArgument,
    IntegerLiteral,
    Loop,
    StringLiteral,
    StructFieldQuery,
    StructFieldUpdate,
    Unresolved,
)

MAIN_FUNCTION = """int main(int argc, char **argv) {
    (void)argc;
    (void)argv;

    struct aaa_stack stack;
    aaa_stack_init(&stack);
    aaa_main(&stack);
    aaa_stack_free(&stack);
}"""


class Transpiler:
    def __init__(
        self, cross_referencer_output: CrossReferencerOutput, output_file: Path
    ) -> None:
        self.output_file = output_file
        self.types = cross_referencer_output.types
        self.functions = cross_referencer_output.functions
        self.builtins_path = cross_referencer_output.builtins_path

    def run(self) -> None:
        code = self._generate_c_file()
        self.output_file.write_text(code)

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

        return (
            includes
            + "\n"
            + forward_func_declarations
            + "\n"
            + content
            + "\n"
            + MAIN_FUNCTION
            + "\n"
        )

    def _generate_c_function_name(self, function: Function) -> str:
        # TODO improve c function name generation a lot
        return "aaa_" + function.name.replace(":", "__")

    def _generate_c_function(self, function: Function) -> str:
        assert not isinstance(function.body, Unresolved)
        assert not isinstance(function.arguments, Unresolved)

        indentation = "    "

        if not function.body:
            return f"// WARNING: no body for function {function.identify()}\n"

        func_name = self._generate_c_function_name(function)

        content = f"void {func_name}(struct aaa_stack *stack) {{\n"

        if function.arguments:
            content += f"{indentation}// load arguments\n"
            for arg in reversed(function.arguments):
                content += f"{indentation}struct aaa_variable {arg.name} = *aaa_stack_pop(stack);\n"
            content += "\n"

        content += self._generate_c_function_body(function.body, 1)
        content += "}\n"

        return content

    def _generate_c_function_body(
        self, function_body: FunctionBody, indent_level: int
    ) -> str:
        code = ""

        for item in function_body.items:
            code += self._generate_c_function_body_item(item, indent_level)

        return code

    def _generate_c_function_body_item(
        self, item: FunctionBodyItem, indent_level: int
    ) -> str:
        indentation = "    " * indent_level

        if isinstance(item, FunctionBody):
            return f"{indentation}// WARNING: FunctionBody is not implemented yet\n"
        elif isinstance(item, IntegerLiteral):
            return f"{indentation}aaa_stack_push_int(stack, {item.value});\n"
        elif isinstance(item, StringLiteral):
            # TODO this is horrible
            string_value = repr(item.value).replace("'", '"')
            return f"{indentation}aaa_stack_push_str(stack, {string_value});\n"
        elif isinstance(item, BooleanLiteral):
            return f"{indentation}// WARNING: BooleanLiteral is not implemented yet\n"
        elif isinstance(item, Loop):
            return self._generate_c_loop(item, indent_level)
        elif isinstance(item, Identifier):
            return self._generate_c_identifier_code(item, indent_level)
        elif isinstance(item, Branch):
            return self._generate_c_branch(item, indent_level)
        elif isinstance(item, StructFieldQuery):
            return f"{indentation}// WARNING: StructFieldQuery is not implemented yet\n"
        elif isinstance(item, StructFieldUpdate):
            return (
                f"{indentation}// WARNING: StructFieldUpdate is not implemented yet\n"
            )
        else:  # pragma: nocover
            assert False

    def _generate_c_loop(self, loop: Loop, indent_level: int) -> str:
        indentation = "    " * indent_level

        code = f"{indentation}while (1) {{\n"
        code += self._generate_c_function_body(loop.condition, indent_level + 1)
        code += f"{indentation}    if (!aaa_stack_pop_bool(stack)) {{\n"
        code += f"{indentation}        break;\n"
        code += f"{indentation}    }}\n"
        code += self._generate_c_function_body(loop.body, indent_level + 1)
        code += f"{indentation}}}\n"

        return code

    def _generate_c_identifier_code(
        self, identifier: Identifier, indent_level: int
    ) -> str:
        indentation = "    " * indent_level

        if isinstance(identifier.kind, IdentifierCallingFunction):
            called = identifier.kind.function

            c_func_name = ""

            if called.file == self.builtins_path:

                aaa_c_builtin_funcs = {
                    ".": "aaa_stack_print",
                    "%": "aaa_stack_modulo",
                    "+": "aaa_stack_plus",
                    "<": "aaa_stack_less",
                    "=": "aaa_stack_equals",
                    "drop": "aaa_stack_drop",
                    "dup": "aaa_stack_dup",
                    "or": "aaa_stack_or",
                }

                try:
                    c_func_name = aaa_c_builtin_funcs[called.name]
                except KeyError:
                    return f"{indentation}// WARNING: Builtin function {identifier.name} is not implemented yet\n"

            else:
                c_func_name = self._generate_c_function_name(called)

            return f"{indentation}{c_func_name}(stack);\n"

        if isinstance(identifier.kind, IdentifierUsingArgument):
            return f"{indentation}aaa_stack_push_variable(stack, &{identifier.name});\n"

        return f"{indentation}// WARNING: Identifier {identifier.name} is not implemented yet\n"

    def _generate_c_branch(self, branch: Branch, indent_level: int) -> str:
        indentation = "    " * indent_level

        code = self._generate_c_function_body(branch.condition, indent_level)
        code += f"{indentation}if (aaa_stack_pop_bool(stack)) {{\n"
        code += self._generate_c_function_body(branch.if_body, indent_level + 1)

        if branch.else_body.items:
            code += f"{indentation}}} else {{\n"
            code += self._generate_c_function_body(branch.else_body, indent_level + 1)

        code += f"{indentation}}}\n"

        return code

from pathlib import Path

from aaa.cross_referencer.models import (
    BooleanLiteral,
    Branch,
    CrossReferencerOutput,
    Function,
    FunctionBody,
    FunctionBodyItem,
    Identifier,
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

        if not function.body:
            return f"// WARNING: no body for function {function.identify()}\n"

        func_name = self._generate_c_function_name(function)

        content = f"void {func_name}(struct aaa_stack *stack) {{\n"
        for item in function.body.items:
            content += self._generate_c_function_body_item(item, 1)
        content += "}\n"

        return content

    def _generate_c_function_body_item(
        self, item: FunctionBodyItem, indent_level: int
    ) -> str:
        indentation = "    " * indent_level

        if isinstance(item, FunctionBody):
            return f"{indentation}// WARNING: FunctionBody is not implemented yet\n"
        elif isinstance(item, IntegerLiteral):
            return f"{indentation}aaa_stack_push_int(stack, {item.value});\n"
        elif isinstance(item, StringLiteral):
            return f"{indentation}// WARNING: StringLiteral is not implemented yet\n"
        elif isinstance(item, BooleanLiteral):
            return f"{indentation}// WARNING: BooleanLiteral is not implemented yet\n"
        elif isinstance(item, Loop):
            return f"{indentation}// WARNING: Loop is not implemented yet\n"
        elif isinstance(item, Identifier):
            return f"{indentation}// WARNING: Identifier is not implemented yet\n"
        elif isinstance(item, Branch):
            return f"{indentation}// WARNING: Branch is not implemented yet\n"
        elif isinstance(item, StructFieldQuery):
            return f"{indentation}// WARNING: StructFieldQuery is not implemented yet\n"
        elif isinstance(item, StructFieldUpdate):
            return (
                f"{indentation}// WARNING: StructFieldUpdate is not implemented yet\n"
            )
        else:  # pragma: nocover
            assert False

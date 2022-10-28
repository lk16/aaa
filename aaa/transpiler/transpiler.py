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
        headers = """
#include <malloc.h>
#include <assert.h>
"""

        aaa_types = """
enum aaa_kind {
    AAA_INTEGER,
    AAA_BOOLEAN,
    AAA_STRING,
    // TODO add more
};

struct aaa_variable {
    enum aaa_kind kind;
    union {
        int integer;
        char *string; // TODO worry about memory leaks
    };
};

struct aaa_stack {
    unsigned size;
    unsigned max_size;
    struct aaa_variable *data;
};

void aaa_stack_init(struct aaa_stack *stack) {
    stack->size = 0;
    stack->max_size = 1024;
    stack->data = malloc(1024 * sizeof(struct aaa_stack));
}

void aaa_stack_free(struct aaa_stack *stack) {
    free(stack->data);
}

void aaa_stack_push_int(struct aaa_stack *stack, int value) {
    assert(stack->size < stack->max_size);

    struct aaa_variable *top = stack->data + stack->size;
    top->kind = AAA_INTEGER;
    top->integer = value;

    stack->size++;
}
        """

        # TODO generate forward declaration of types

        # TODO generate type definitions

        # TODO generate forward declarations of functions

        content = ""

        for function in self.functions.values():
            if function.file == self.builtins_path:
                continue
            content += self._generate_c_function(function)
            content += "\n"

        main_function = """
int main(int argc, char **argv) {
    (void)argc;
    (void)argv;

    struct aaa_stack stack;
    aaa_stack_init(&stack);
    aaa_main(&stack);
    aaa_stack_free(&stack);
}
        """

        return (
            headers.strip()
            + "\n\n"
            + aaa_types.strip()
            + "\n\n"
            + content.strip()
            + "\n\n"
            + main_function.strip()
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

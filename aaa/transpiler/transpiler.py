import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

from aaa.cross_referencer.models import (
    Assignment,
    BooleanLiteral,
    Branch,
    CallArgument,
    CallFunction,
    CallType,
    CallVariable,
    CrossReferencerOutput,
    ForeachLoop,
    Function,
    FunctionBody,
    FunctionBodyItem,
    IntegerLiteral,
    StringLiteral,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
    UseBlock,
    VariableType,
    WhileLoop,
)
from aaa.type_checker.models import TypeCheckerOutput

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
        self,
        cross_referencer_output: CrossReferencerOutput,
        type_checker_output: TypeCheckerOutput,
        generated_c_file: Optional[Path],
        generated_binary_file: Optional[Path],
        verbose: bool,
    ) -> None:
        self.types = cross_referencer_output.types
        self.functions = cross_referencer_output.functions
        self.builtins_path = cross_referencer_output.builtins_path
        self.entrypoint = cross_referencer_output.entrypoint
        self.foreach_loop_stacks = type_checker_output.foreach_loop_stacks
        self.verbose = verbose  # TODO use

        self.generated_c_file = generated_c_file or Path(
            NamedTemporaryFile(delete=False, suffix=".c").name
        )

        self.generated_binary_file = generated_binary_file or Path(
            NamedTemporaryFile(delete=False).name
        )

    def _build_stdlib(self) -> int:
        proc = subprocess.run(["cmake", "."], cwd=("./c"), capture_output=True)
        exit_code = proc.returncode

        if exit_code != 0:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)
            return exit_code

        proc = subprocess.run(["make"], cwd=("./c"), capture_output=True)

        if exit_code != 0:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)

        return exit_code

    def run(self, compile: bool, run_binary: bool) -> int:
        code = self._generate_c_file()
        self.generated_c_file.write_text(code)

        if compile:  # pragma: nocover
            exit_code = self._build_stdlib()
            if exit_code != 0:
                return exit_code

            command = [
                "gcc",
                # "--coverage", TODO enable this flag with flag
                "-I",
                "./c/",
                str(self.generated_c_file),
                "./c/libaaa_stdlib.a",
                "-o",
                str(self.generated_binary_file),
                "-std=gnu99",
                "-g",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-Wcast-align",
                "-Wconversion",
                "-Wfloat-equal",
                "-Wformat=2",
                "-Winline",
                "-Wlogical-op",
                "-Wmissing-prototypes",
                "-Wno-missing-braces",
                "-Wno-missing-field-initializers",
                "-Wold-style-definition",
                "-Wpointer-arith",
                "-Wredundant-decls",
                "-Wshadow",
                "-Wstrict-prototypes",
                "-Wswitch-default",
                "-Wswitch-enum",
                "-Wundef",
                "-Wunreachable-code",
            ]

            exit_code = subprocess.run(command).returncode

            if exit_code != 0:
                return exit_code

        if run_binary:  # pragma: nocover
            return subprocess.run([self.generated_binary_file]).returncode

        return 0

    def _indent(self, indent: int) -> str:
        return C_IDENTATION * indent

    def _generate_c_file(self) -> str:
        content = '#include "aaa.h"\n'
        content += "\n"

        for type in self.types.values():
            content += self._generate_c_struct_new_func_prototype(type)

        content += "\n"

        for type in self.types.values():
            content += self._generate_c_struct_new_func(type)

        for function in self.functions.values():
            if function.position.file == self.builtins_path:
                continue
            func_name = self._generate_c_function_name(function)
            content += f"void {func_name}(struct aaa_stack *stack);\n"

        content += "\n"

        for function in self.functions.values():
            if function.position.file == self.builtins_path:
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
        return self._generate_c_builtin_function_name_from_str(function.name)

    def _generate_c_builtin_function_name_from_str(self, name: str) -> str:
        if name in AAA_C_BUILTIN_FUNCS:
            return AAA_C_BUILTIN_FUNCS[name]

        return "aaa_stack_" + name.replace(":", "_")

    def _generate_c_function_name(self, function: Function) -> str:
        if function.position.file == self.builtins_path:
            return self._generate_c_builtin_function_name(function)

        # hash file and name to prevent naming collisions
        hash_input = f"{function.position.file} {function.name}"
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]
        return f"aaa_user_func_{hash}"

    def _get_member_function(self, var_type: VariableType, func_name: str) -> Function:
        # TODO this assumes the func is defined in same file as type
        file = var_type.type.position.file
        name = f"{var_type.name}:{func_name}"
        return self.functions[(file, name)]

    def _generate_c_function(self, function: Function) -> str:
        indentation = "    "

        assert function.body

        func_name = self._generate_c_function_name(function)

        content = f"// Generated from: {function.position.file} {function.name}\n"
        content += f"void {func_name}(struct aaa_stack *stack) {{\n"

        if function.arguments:
            content += f"{indentation}// load arguments\n"
            for arg in reversed(function.arguments):
                content += f"{indentation}struct aaa_variable *aaa_arg_{arg.name} = aaa_stack_pop(stack);\n"
            content += "\n"

        content += self._generate_c_function_body(function.body, 1)

        if function.arguments:
            content += "\n"
            content += f"{indentation}// decrease arguments' ref_count\n"
            for arg in reversed(function.arguments):
                content += f"{indentation}aaa_variable_dec_ref(aaa_arg_{arg.name});\n"

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

        if isinstance(item, IntegerLiteral):
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
        elif isinstance(item, WhileLoop):
            return self._generate_c_while_loop(item, indent)
        elif isinstance(item, ForeachLoop):
            return self._generate_c_foreach_loop(item, indent)
        elif isinstance(item, CallFunction):
            return self._generate_c_call_function_code(item, indent)
        elif isinstance(item, CallType):
            return self._generate_c_call_type_code(item, indent)
        elif isinstance(item, CallArgument):
            return self._generate_c_call_argument_code(item, indent)
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
        elif isinstance(item, UseBlock):
            return self._generate_c_use_block_code(item, indent)
        elif isinstance(item, CallVariable):
            return self._generate_c_call_variable_code(item, indent)
        elif isinstance(item, Assignment):
            return self._generate_c_assignment_code(item, indent)
        else:  # pragma: nocover
            assert False

    def _generate_c_while_loop(self, while_loop: WhileLoop, indent: int) -> str:
        condition_code = self._generate_c_function_body(
            while_loop.condition, indent + 1
        )
        body_code = self._generate_c_function_body(while_loop.body, indent + 1)

        return (
            f"{self._indent(indent)}while (true) {{\n"
            + condition_code
            + f"{self._indent(indent+1)}if (!aaa_stack_pop_bool(stack)) {{\n"
            + f"{self._indent(indent+2)}break;\n"
            + f"{self._indent(indent+1)}}}\n"
            + body_code
            + f"{self._indent(indent)}}}\n"
        )

    def _generate_c_foreach_loop(self, foreach_loop: ForeachLoop, indent: int) -> str:
        """
        dup iterable
        iter

        while (true) {
            dup iterator
            next
            if popped boolean is true {
                drop everything `next` added
                drop iterator
                break
            }
            loop body
        }
        drop iterable
        """

        # If any of these next two lines fail, TypeChecker is broken.
        stack = self.foreach_loop_stacks[foreach_loop.position]
        iterable_type = stack[-1]

        iter_func = self._get_member_function(iterable_type, "iter")
        iterator_type = iter_func.return_types[0]
        next_func = self._get_member_function(iterator_type, "next")

        dup = self._generate_c_builtin_function_name_from_str("dup")
        drop = self._generate_c_builtin_function_name_from_str("drop")
        iter = self._generate_c_function_name(iter_func)
        next = self._generate_c_function_name(next_func)
        break_drop_count = len(next_func.return_types)

        output = ""
        output += f"{self._indent(indent)}{dup}(stack);\n"
        output += f"{self._indent(indent)}{iter}(stack);\n"
        output += f"{self._indent(indent)}while (true) {{\n"
        output += f"{self._indent(indent+1)}{dup}(stack);\n"
        output += f"{self._indent(indent+1)}{next}(stack);\n"
        output += f"{self._indent(indent+1)}if (!aaa_stack_pop_bool(stack)) {{\n"

        for _ in range(break_drop_count):
            output += f"{self._indent(indent+2)}{drop}(stack);\n"

        output += f"{self._indent(indent+2)}break;\n"
        output += f"{self._indent(indent+1)}}}\n"
        output += self._generate_c_function_body(foreach_loop.body, indent + 1)
        output += f"{self._indent(indent)}}}\n"
        output += f"{self._indent(indent)}{drop}(stack);\n"

        return output

    def _generate_c_call_function_code(
        self, call_func: CallFunction, indent: int
    ) -> str:
        indentation = self._indent(indent)
        called = call_func.function
        c_func_name = self._generate_c_function_name(called)

        return f"{indentation}{c_func_name}(stack);\n"

    def _generate_c_call_type_code(self, call_type: CallType, indent: int) -> str:
        indentation = self._indent(indent)
        var_type = call_type.var_type

        if var_type.type.position.file == self.builtins_path:
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
            elif var_type.name == "set":
                return f"{indentation}aaa_stack_push_set_empty(stack);\n"
            else:  # pragma: nocover
                assert False

        c_struct_name = self._generate_c_struct_name(var_type.type)
        return f"{indentation}aaa_stack_push_struct(stack, {c_struct_name}_new());\n"

    def _generate_c_call_argument_code(
        self, call_arg: CallArgument, indent: int
    ) -> str:
        indentation = self._indent(indent)
        arg_name = call_arg.argument.name

        return (
            f"{indentation}aaa_variable_inc_ref(aaa_arg_{arg_name});\n"
            + f"{indentation}aaa_stack_push(stack, aaa_arg_{arg_name});\n"
        )

    def _generate_c_branch(self, branch: Branch, indent: int) -> str:
        indentation = self._indent(indent)

        condition_code = self._generate_c_function_body(branch.condition, indent)
        if_code = self._generate_c_function_body(branch.if_body, indent + 1)

        code = (
            condition_code
            + f"{indentation}if (aaa_stack_pop_bool(stack)) {{\n"
            + if_code
        )

        if branch.else_body:
            else_code = self._generate_c_function_body(branch.else_body, indent + 1)
            code += f"{indentation}}} else {{\n" + else_code

        code += f"{indentation}}}\n"

        return code

    def _generate_c_struct_name(self, type: Type) -> str:
        hash_input = f"{type.position.file} {type.name}"
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]
        return f"aaa_user_struct_{hash}"

    def _generate_c_struct_new_func_prototype(self, type: Type) -> str:
        if type.position.file == self.builtins_path and not type.fields:
            return ""

        c_struct_name = self._generate_c_struct_name(type)
        return f"struct aaa_struct *{c_struct_name}_new(void);\n"

    def _generate_c_struct_new_func(self, type: Type) -> str:
        if type.position.file == self.builtins_path and not type.fields:
            return ""

        c_struct_name = self._generate_c_struct_name(type)

        code = f"// Generated for: {type.position.file} {type.name}\n"
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
                c_field_struct_name = self._generate_c_struct_name(field_type.type)
                code += f"aaa_variable_new_struct({c_field_struct_name}_new());\n"

            code += f'{C_IDENTATION}aaa_struct_create_field(s, "{field_name}", {field_name});\n'
            code += f"{C_IDENTATION}aaa_variable_dec_ref({field_name});\n"

        code += f"{C_IDENTATION}return s;\n"
        code += "}\n\n"

        return code

    def _generate_c_use_block_code(self, use_block: UseBlock, indent: int) -> str:
        code = f"{self._indent(indent)}{{\n"
        for var in reversed(use_block.variables):
            code += f"{self._indent(indent+1)}struct aaa_variable *aaa_local_{var.name} = aaa_stack_pop(stack);\n"

        code += self._generate_c_function_body(use_block.body, indent + 1)

        for var in use_block.variables:
            code += (
                f"{self._indent(indent+1)}aaa_variable_dec_ref(aaa_local_{var.name});\n"
            )

        code += f"{self._indent(indent)}}}\n"
        return code

    def _generate_c_call_variable_code(
        self, call_var: CallVariable, indent: int
    ) -> str:
        indentation = self._indent(indent)
        var_name = call_var.variable.name

        return (
            f"{indentation}aaa_variable_inc_ref(aaa_local_{var_name});\n"
            + f"{indentation}aaa_stack_push(stack, aaa_local_{var_name});\n"
        )

    def _generate_c_assignment_code(self, assignment: Assignment, indent: int) -> str:
        code = self._generate_c_function_body(assignment.body, indent)

        for var in reversed(assignment.variables):
            code += f"{self._indent(indent)}aaa_variable_assign(aaa_local_{var.name}, aaa_stack_pop(stack));\n"

        return code

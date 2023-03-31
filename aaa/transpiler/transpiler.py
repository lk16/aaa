import subprocess
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, Set

from aaa.cross_referencer.models import (
    Assignment,
    BooleanLiteral,
    Branch,
    CallFunction,
    CallType,
    CallVariable,
    CaseBlock,
    CrossReferencerOutput,
    DefaultBlock,
    ForeachLoop,
    Function,
    FunctionBody,
    FunctionBodyItem,
    IntegerLiteral,
    MatchBlock,
    Never,
    Return,
    StringLiteral,
    StructFieldQuery,
    StructFieldUpdate,
    Type,
    UseBlock,
    VariableType,
    WhileLoop,
)
from aaa.type_checker.models import TypeCheckerOutput

AAA_RUST_BUILTIN_FUNCS = {
    "-": "minus",
    "!=": "unequal",
    ".": "print",
    "*": "multiply",
    "/": "divide",
    "%": "modulo",
    "+": "plus",
    "<": "less",
    "<=": "less_equal",
    "=": "equals",
    ">": "greater",
    ">=": "greater_equal",
}


class Transpiler:
    def __init__(
        self,
        cross_referencer_output: CrossReferencerOutput,
        type_checker_output: TypeCheckerOutput,
        generated_binary_file: Optional[Path],
        verbose: bool,
    ) -> None:
        self.types = cross_referencer_output.types
        self.functions = cross_referencer_output.functions
        self.builtins_path = cross_referencer_output.builtins_path
        self.entrypoint = cross_referencer_output.entrypoint
        self.foreach_loop_stacks = type_checker_output.foreach_loop_stacks
        self.func_local_vars: Set[str] = set()
        self.verbose = verbose
        self.indent_level = 0

        self.transpiled_rust_root = Path("/tmp/transpiled")

        self.generated_binary_file = (
            generated_binary_file
            or Path(NamedTemporaryFile(delete=False).name).resolve()
        )

    def run(self, compile: bool, run_binary: bool) -> int:
        # TODO clean this up
        src_folder = self.transpiled_rust_root / "src"
        src_folder.mkdir(parents=True, exist_ok=True)
        cargo_file = (self.transpiled_rust_root / "Cargo.toml").resolve()
        aaa_stdlib_impl_path = (Path(__file__).parent / "../../aaa-stdlib").resolve()

        cargo_file.write_text(
            "[package]\n"
            + 'name = "aaa-stdlib-user"\n'
            + 'version = "0.1.0"\n'
            + 'edition = "2021"\n'
            + "\n"
            + "# See more keys and their definitions at https://doc.rust-lang.org/cargo/reference/manifest.html\n"
            + "\n"
            + "[dependencies]\n"
            + f'aaa-stdlib = {{ version = "0.1.0", path = "{aaa_stdlib_impl_path}" }}\n'
        )

        code = self._generate_rust_file()

        Path(self.transpiled_rust_root / "src/main.rs").write_text(code)

        if compile:  # pragma: nocover
            command = ["cargo", "build", "--quiet", "--manifest-path", str(cargo_file)]
            exit_code = subprocess.run(command).returncode

            if exit_code != 0:
                return exit_code

            binary_file = self.transpiled_rust_root / "target/debug/aaa-stdlib-user"
            binary_file.rename(self.generated_binary_file)

        if run_binary:  # pragma: nocover
            command = [str(self.generated_binary_file)]
            return subprocess.run(command).returncode

        return 0

    def _indent(self, line: str) -> str:
        indentation = "    " * self.indent_level
        return indentation + line

    def _generate_rust_file(self) -> str:
        content = "use aaa_stdlib::stack::Stack;\n"
        content += "\n"

        # TODO generate code for types

        for function in self.functions.values():
            if function.position.file == self.builtins_path:
                continue
            content += self._generate_rust_function(function)

        content += self._generate_rust_main_function()

        return content

    def _generate_rust_main_function(self) -> str:
        # TODO handle argv and return code

        main_func = self.functions[(self.entrypoint, "main")]
        main_func_name = self._generate_rust_function_name(main_func)

        code = "fn main() {\n"
        self.indent_level += 1
        code += self._indent("let mut stack = Stack::new();\n")
        code += self._indent(f"{main_func_name}(&mut stack);\n")

        self.indent_level -= 1
        code += "}\n"

        return code

    def _generate_rust_builtin_function_name(self, function: Function) -> str:
        return self._generate_rust_builtin_function_name_from_str(function.name)

    def _generate_rust_builtin_function_name_from_str(self, name: str) -> str:
        if name in AAA_RUST_BUILTIN_FUNCS:
            return AAA_RUST_BUILTIN_FUNCS[name]

        return name.replace(":", "_")

    def _generate_rust_function_name(self, function: Function) -> str:
        if function.position.file == self.builtins_path:
            return "stack." + self._generate_rust_builtin_function_name(function)

        # TODO consider using modules in generated code so we don't have to hash at all

        # hash file and name to prevent naming collisions
        hash_input = f"{function.position.file} {function.name}"
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]

        if function.is_enum_ctor:
            return f"enum_ctor_func_{hash}"
        return f"user_func_{hash}"

    def _get_member_function(self, var_type: VariableType, func_name: str) -> Function:
        # NOTE It is required that member funcitions are
        # defined in same file as the type they operate on.
        file = var_type.type.position.file
        name = f"{var_type.name}:{func_name}"
        return self.functions[(file, name)]

    def _generate_rust_enum_ctor_function(self, function: Function) -> str:
        func_name = self._generate_rust_function_name(function)

        enum_type_key = (function.position.file, function.struct_name)
        enum_type = self.types[enum_type_key]
        variant_id = enum_type.enum_fields[function.func_name][1]

        content = f"// Generated for: {function.position.file} enum {function.struct_name}, variant {function.func_name}\n"
        content += f"void {func_name}(struct aaa_stack *stack) {{\n"

        self.indent_level += 1

        content += self._indent("struct aaa_variable *var = aaa_stack_pop(stack);\n")
        content += self._indent(
            f"struct aaa_variable *enum_var = aaa_variable_new_enum(var, {variant_id});\n"
        )
        content += self._indent("aaa_stack_push(stack, enum_var);\n")

        self.indent_level -= 1

        content += "}\n\n"

        return content

    def _generate_rust_function(self, function: Function) -> str:
        if function.is_enum_ctor:
            return self._generate_rust_enum_ctor_function(function)

        assert function.body
        self.func_local_vars = set()

        func_name = self._generate_rust_function_name(function)

        content = f"// Generated from: {function.position.file} {function.name}\n"
        content += f"fn {func_name}(stack: &mut Stack) {{\n"

        self.indent_level += 1

        if function.arguments:
            content += self._indent("// load arguments\n")
            for arg in reversed(function.arguments):
                content += self._indent(f"let var_{arg.name} = stack.pop();\n")
                self.func_local_vars.add(arg.name)
            content += "\n"

        content += self._generate_rust_function_body(function.body)

        self.indent_level -= 1
        content += "}\n\n"

        return content

    def _generate_rust_function_body(self, function_body: FunctionBody) -> str:
        code = ""

        for item in function_body.items:
            code += self._generate_rust_function_body_item(item)

        return code

    def _generate_rust_function_body_item(self, item: FunctionBodyItem) -> str:
        if isinstance(item, IntegerLiteral):
            return self._indent(f"stack.push_int({item.value});\n")
        elif isinstance(item, StringLiteral):
            return self._generate_rust_string_literal(item)
        elif isinstance(item, BooleanLiteral):
            bool_value = "true"
            if not item.value:
                bool_value = "false"
            return self._indent(f"stack.push_bool({bool_value});\n")
        elif isinstance(item, WhileLoop):
            return self._generate_rust_while_loop(item)
        elif isinstance(item, ForeachLoop):
            return self._generate_rust_foreach_loop(item)
        elif isinstance(item, CallFunction):
            return self._generate_rust_call_function_code(item)
        elif isinstance(item, CallType):
            return self._generate_rust_call_type_code(item)
        elif isinstance(item, Branch):
            return self._generate_rust_branch(item)
        elif isinstance(item, StructFieldQuery):
            return self._indent(
                f'aaa_stack_push_str_raw(stack, "{item.field_name.value}", false);\n'
            ) + self._indent("aaa_stack_field_query(stack);\n")
        elif isinstance(item, StructFieldUpdate):
            return (
                self._indent(
                    f'aaa_stack_push_str_raw(stack, "{item.field_name.value}", false);\n'
                )
                + self._generate_rust_function_body(item.new_value_expr)
                + self._indent(f"aaa_stack_field_update(stack);\n")
            )
        elif isinstance(item, UseBlock):
            return self._generate_rust_use_block_code(item)
        elif isinstance(item, CallVariable):
            return self._generate_rust_call_variable_code(item)
        elif isinstance(item, Assignment):
            return self._generate_rust_assignment_code(item)
        elif isinstance(item, Return):
            return self._generate_rust_return(item)
        elif isinstance(item, MatchBlock):
            return self._generate_rust_match_block_code(item)
        else:  # pragma: nocover
            assert False

    def _generate_rust_match_block_code(self, match_block: MatchBlock) -> str:
        # Use hash suffix for variables to prevent name colission
        hash_input = str(match_block.position)
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]

        code = self._indent(
            f"struct aaa_variable *enum_{hash} = aaa_stack_pop(stack);\n"
        )
        code += self._indent(
            f"int variant_id_{hash} = aaa_variable_get_enum_variant_id(enum_{hash});\n"
        )
        code += self._indent(
            f"struct aaa_variable *enum_value_{hash} = aaa_variable_get_enum_value(enum_{hash});\n"
        )
        code += self._indent(f"aaa_variable_inc_ref(enum_value_{hash});\n")
        code += self._indent(f"aaa_stack_push(stack, enum_value_{hash});\n")

        code += self._indent(f"aaa_variable_dec_ref(enum_{hash});\n")

        code += self._indent(f"switch (variant_id_{hash}) {{\n")
        self.indent_level += 1

        has_default = False

        for block in match_block.blocks:
            if isinstance(block, CaseBlock):
                code += self._generate_rust_case_block_code(block)
            elif isinstance(block, DefaultBlock):
                has_default = True
                code += self._generate_rust_default_block_code(block)
            else:  # pragma: nocover
                assert False

        if not has_default:
            code += self._indent("default:\n")

            self.indent_level += 1
            code += self._indent("break;\n")
            self.indent_level -= 1

        self.indent_level -= 1

        code += self._indent("}\n")

        return code

    def _generate_rust_case_block_code(self, case_block: CaseBlock) -> str:
        enum_type = case_block.enum_type
        variant_id = enum_type.enum_fields[case_block.variant_name][1]

        code = self._indent(
            f"case {variant_id}: // {enum_type.name}:{case_block.variant_name}\n"
        )
        self.indent_level += 1
        code += self._generate_rust_function_body(case_block.body)
        code += self._indent("break;\n")
        self.indent_level -= 1

        return code

    def _generate_rust_default_block_code(self, default_block: DefaultBlock) -> str:
        code = self._indent(f"default:\n")
        self.indent_level += 1
        code += self._indent("aaa_stack_drop(stack);\n")
        code += self._generate_rust_function_body(default_block.body)
        code += self._indent("break;\n")
        self.indent_level -= 1

        return code

    def _generate_rust_return(self, return_: Return) -> str:
        code = ""

        for local_var_name in self.func_local_vars:
            code += self._indent(f"aaa_variable_dec_ref(aaa_local_{local_var_name});\n")

        code += self._indent("return;\n")
        return code

    def _generate_rust_string_literal(self, string_literal: StringLiteral) -> str:
        string_value = repr(string_literal.value)[1:-1].replace('"', '\\"')
        return self._indent(f'stack.push_str(String::from("{string_value}"));\n')

    def _generate_rust_while_loop(self, while_loop: WhileLoop) -> str:

        code = self._indent("loop {\n")
        self.indent_level += 1

        code += self._generate_rust_function_body(while_loop.condition)

        code += self._indent("if !stack.pop_bool() {\n")
        self.indent_level += 1

        code += self._indent("break;\n")

        self.indent_level -= 1
        code += self._indent("}\n")

        code += self._generate_rust_function_body(while_loop.body)

        self.indent_level -= 1
        code += self._indent("}\n")

        return code

    def _generate_rust_foreach_loop(self, foreach_loop: ForeachLoop) -> str:
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

        if iterable_type.is_const:
            iter_func = self._get_member_function(iterable_type, "const_iter")
        else:
            iter_func = self._get_member_function(iterable_type, "iter")

        assert not isinstance(iter_func.return_types, Never)

        iterator_type = iter_func.return_types[0]
        next_func = self._get_member_function(iterator_type, "next")
        assert not isinstance(next_func.return_types, Never)

        dup = self._generate_rust_builtin_function_name_from_str("dup")
        drop = self._generate_rust_builtin_function_name_from_str("drop")
        iter = self._generate_rust_function_name(iter_func)
        next = self._generate_rust_function_name(next_func)
        break_drop_count = len(next_func.return_types)

        code = ""
        code += self._indent(f"{dup}(stack);\n")
        code += self._indent(f"{iter}(stack);\n")

        code += self._indent("while (true) {\n")
        self.indent_level += 1

        code += self._indent(f"{dup}(stack);\n")
        code += self._indent(f"{next}(stack);\n")

        code += self._indent("if (!aaa_stack_pop_bool(stack)) {\n")
        self.indent_level += 1

        for _ in range(break_drop_count):
            code += self._indent(f"{drop}(stack);\n")

        code += self._indent(f"break;\n")

        self.indent_level -= 1
        code += self._indent("}\n")

        code += self._generate_rust_function_body(foreach_loop.body)

        self.indent_level -= 1
        code += self._indent("}\n")

        code += self._indent(f"{drop}(stack);\n")

        return code

    def _generate_rust_call_function_code(self, call_func: CallFunction) -> str:
        called = call_func.function
        rust_func_name = self._generate_rust_function_name(called)

        if called.position.file == self.builtins_path:
            return self._indent(f"{rust_func_name}();\n")

        return self._indent(f"{rust_func_name}(stack);\n")

    def _generate_rust_call_type_code(self, call_type: CallType) -> str:
        var_type = call_type.var_type

        if var_type.type.position.file == self.builtins_path:
            if var_type.name == "int":
                return self._indent("aaa_stack_push_int(stack, 0);\n")
            elif var_type.name == "str":
                return self._indent('aaa_stack_push_str_raw(stack, "", false);\n')
            elif var_type.name == "bool":
                return self._indent("aaa_stack_push_bool(stack, false);\n")
            elif var_type.name == "vec":
                return self._indent("aaa_stack_push_vec_empty(stack);\n")
            elif var_type.name == "map":
                return self._indent("aaa_stack_push_map_empty(stack);\n")
            elif var_type.name == "set":
                return self._indent("aaa_stack_push_set_empty(stack);\n")
            else:  # pragma: nocover
                assert False

        c_struct_name = self._generate_rust_struct_name(var_type.type)
        return self._indent(f"aaa_stack_push_struct(stack, {c_struct_name}_new());\n")

    def _generate_rust_branch(self, branch: Branch) -> str:
        code = self._generate_rust_function_body(branch.condition)

        code += self._indent("if stack.pop_bool() {\n")
        self.indent_level += 1

        code += self._generate_rust_function_body(branch.if_body)

        if branch.else_body:
            self.indent_level -= 1
            code += self._indent("} else {\n")
            self.indent_level += 1

            code += self._generate_rust_function_body(branch.else_body)

        self.indent_level -= 1
        code += self._indent("}\n")

        return code

    def _generate_rust_struct_name(self, type: Type) -> str:
        hash_input = f"{type.position.file} {type.name}"
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]
        return f"aaa_user_struct_{hash}"

    def _generate_rust_struct_new_func_prototype(self, type: Type) -> str:
        if type.position.file == self.builtins_path and not type.fields:
            return ""

        c_struct_name = self._generate_rust_struct_name(type)
        return f"struct aaa_struct *{c_struct_name}_new(void);\n"

    def _generate_rust_struct_new_func(self, type: Type) -> str:
        if type.position.file == self.builtins_path and not type.fields:
            return ""

        c_struct_name = self._generate_rust_struct_name(type)

        code = f"// Generated for: {type.position.file} {type.name}\n"
        code += f"struct aaa_struct *{c_struct_name}_new(void) {{\n"

        self.indent_level += 1
        code += self._indent(f'struct aaa_struct *s = aaa_struct_new("{type.name}");\n')

        for field_name, field_type in type.fields.items():
            code += self._indent(f"struct aaa_variable *{field_name} = ")
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
                c_field_struct_name = self._generate_rust_struct_name(field_type.type)
                code += f"aaa_variable_new_struct({c_field_struct_name}_new());\n"

            code += self._indent(
                f'aaa_struct_create_field(s, "{field_name}", {field_name});\n'
            )
            code += self._indent(f"aaa_variable_dec_ref({field_name});\n")

        code += self._indent("return s;\n")

        self.indent_level -= 1
        code += "}\n\n"

        return code

    def _generate_rust_use_block_code(self, use_block: UseBlock) -> str:

        code = self._indent("{\n")
        self.indent_level += 1

        for var in reversed(use_block.variables):
            code += self._indent(
                f"struct aaa_variable *aaa_local_{var.name} = aaa_stack_pop(stack);\n"
            )
            self.func_local_vars.add(var.name)

        code += self._generate_rust_function_body(use_block.body)

        for var in use_block.variables:
            code += self._indent(f"aaa_variable_dec_ref(aaa_local_{var.name});\n")
            self.func_local_vars.remove(var.name)

        self.indent_level -= 1
        code += self._indent("}\n")

        return code

    def _generate_rust_call_variable_code(self, call_var: CallVariable) -> str:
        name = call_var.name
        return self._indent(f"stack.push(var_{name}.clone());\n")

    def _generate_rust_assignment_code(self, assignment: Assignment) -> str:
        code = self._generate_rust_function_body(assignment.body)

        for var in reversed(assignment.variables):
            code += self._indent(
                f"aaa_stack_variable_assign(stack, aaa_local_{var.name});\n"
            )

        return code

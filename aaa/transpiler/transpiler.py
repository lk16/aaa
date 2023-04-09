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
        self.position_stacks = type_checker_output.position_stacks
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
        content = "#![allow(unused_imports)]\n"
        content += "#![allow(unused_mut)]\n"
        content += "\n"
        content += "use aaa_stdlib::map::Map;\n"
        content += "use aaa_stdlib::stack::Stack;\n"
        content += "use aaa_stdlib::set::Set;\n"
        content += "use aaa_stdlib::var::{Struct, Variable};\n"
        content += "use aaa_stdlib::vector::Vector;\n"
        content += "use std::cell::RefCell;\n"
        content += "use std::collections::HashMap;\n"
        content += "use std::rc::Rc;\n"

        content += "\n"

        for type in self.types.values():
            content += self._generate_rust_struct_new_func(type)

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
            return self._generate_rust_field_query_code(item)
        elif isinstance(item, StructFieldUpdate):
            return self._generate_rust_field_update_code(item)
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

    def _generate_rust_field_query_code(self, field_query: StructFieldQuery) -> str:
        field_name = field_query.field_name.value
        return self._indent(f'stack.struct_field_query("{field_name}");\n')

    def _generate_rust_field_update_code(self, field_update: StructFieldUpdate) -> str:
        field_name = field_update.field_name.value

        code = self._generate_rust_function_body(field_update.new_value_expr)
        code += self._indent(f'stack.struct_field_update("{field_name}");\n')
        return code

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
        stack = self.position_stacks[foreach_loop.position]

        # NOTE: The typechecker prevents this from being `never`
        assert not isinstance(stack, Never)

        iterable_type = stack[-1]

        if iterable_type.is_const:
            iter_func = self._get_member_function(iterable_type, "const_iter")
        else:
            iter_func = self._get_member_function(iterable_type, "iter")

        assert not isinstance(iter_func.return_types, Never)

        iterator_type = iter_func.return_types[0]
        next_func = self._get_member_function(iterator_type, "next")
        assert not isinstance(next_func.return_types, Never)

        iter = self._generate_rust_function_name(iter_func)
        next = self._generate_rust_function_name(next_func)
        break_drop_count = len(next_func.return_types)

        code = ""
        code += self._indent(f"stack.dup();\n")

        if iter_func.position.file == self.builtins_path:
            code += self._indent(f"{iter}();\n")
        else:
            code += self._indent(f"{iter}(stack);\n")

        code += self._indent("loop {\n")
        self.indent_level += 1

        code += self._indent(f"stack.dup();\n")
        if iter_func.position.file == self.builtins_path:
            code += self._indent(f"{next}();\n")
        else:
            code += self._indent(f"{next}(stack);\n")

        code += self._indent("if !stack.pop_bool() {\n")
        self.indent_level += 1

        for _ in range(break_drop_count):
            code += self._indent(f"stack.drop();\n")

        code += self._indent(f"break;\n")

        self.indent_level -= 1
        code += self._indent("}\n")

        code += self._generate_rust_function_body(foreach_loop.body)

        self.indent_level -= 1
        code += self._indent("}\n")

        code += self._indent(f"stack.drop();\n")

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
                return self._indent("stack.push_int(0);\n")
            elif var_type.name == "str":
                return self._indent('stack.push_str(String::from(""));\n')
            elif var_type.name == "bool":
                return self._indent("stack.push_bool(false);\n")
            elif var_type.name == "vec":
                return self._indent("stack.push_vector(Vector::new());\n")
            elif var_type.name == "map":
                return self._indent("stack.push_map(Map::new());\n")
            elif var_type.name == "set":
                return self._indent("stack.push_set(Set::new());\n")
            else:  # pragma: nocover
                assert False

        rust_struct_name = self._generate_rust_struct_name(var_type.type)
        return self._indent(f"stack.push_struct({rust_struct_name}_new());\n")

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
        return f"user_struct_{hash}"

    def _generate_rust_struct_new_func(self, type: Type) -> str:
        if type.position.file == self.builtins_path and not type.fields:
            return ""

        c_struct_name = self._generate_rust_struct_name(type)

        code = f"// Generated for: {type.position.file} {type.name}\n"
        code += f"fn {c_struct_name}_new() -> Struct {{\n"

        self.indent_level += 1
        code += self._indent(f'let type_name = String::from("{type.name}");\n')
        code += self._indent("let values = HashMap::from([\n")

        self.indent_level += 1

        for field_name, field_type in type.fields.items():
            if field_type.name == "int":
                value = "Variable::Integer(0)"
            elif field_type.name == "bool":
                value = "Variable::Boolean(false)"
            elif field_type.name == "str":
                value = 'Variable::String(Rc::new(RefCell::new(String::from(""))))'
            elif field_type.name == "vec":
                value = "Variable::Vector(Rc::new(RefCell::new(Vector::new())))"
            elif field_type.name == "map":
                value = "Variable::Map(Rc::new(RefCell::new(Map::new())))"
            elif field_type.name == "set":
                value = "Variable::Set(Rc::new(RefCell::new(Set::new())))"
            else:
                rust_struct_name = self._generate_rust_struct_name(field_type.type)
                value = (
                    f"Variable::Struct(Rc::new(RefCell::new({rust_struct_name}_new())))"
                )

            code += self._indent(f'(String::from("{field_name}"), {value}),\n')

        self.indent_level -= 1

        code += self._indent("]);\n")
        code += self._indent("Struct { type_name, values }\n")

        self.indent_level -= 1
        code += "}\n\n"

        return code

    def _generate_rust_use_block_code(self, use_block: UseBlock) -> str:

        code = self._indent("{\n")
        self.indent_level += 1

        for var in reversed(use_block.variables):
            code += self._indent(f"let mut var_{var.name} = stack.pop();\n")
            self.func_local_vars.add(var.name)

        code += self._generate_rust_function_body(use_block.body)

        for var in use_block.variables:
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
            code += self._indent(f"stack.assign(&mut var_{var.name});\n")

        return code

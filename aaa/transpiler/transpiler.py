import subprocess
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional, Set

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

CARGO_TOML_TEMPLATE = """
[package]
name = "aaa-stdlib-user"
version = "0.1.0"
edition = "2021"
# See more keys and their definitions at https://doc.rust-lang.org/cargo/reference/manifest.html

[dependencies]
aaa-stdlib = {{ version = "0.1.0", path = "{stdlib_impl_path}" }}
regex = "1.8.4"
"""


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

    def get_stdlib_impl_path(self) -> Path:
        return (Path(__file__).parent / "../../aaa-stdlib").resolve()

    def get_cargo_toml_path(self) -> Path:
        return (self.transpiled_rust_root / "Cargo.toml").resolve()

    def get_generated_source_path(self) -> Path:
        return Path(self.transpiled_rust_root / "src/main.rs")

    def run(self, compile: bool, run_binary: bool, args: List[str]) -> int:
        generated_rust_file = self.get_generated_source_path()
        cargo_toml = self.get_cargo_toml_path()
        stdlib_impl_path = self.get_stdlib_impl_path()

        generated_rust_file.parent.mkdir(parents=True, exist_ok=True)

        cargo_toml.write_text(
            CARGO_TOML_TEMPLATE.format(stdlib_impl_path=stdlib_impl_path)
        )

        code = self._generate_rust_file()

        generated_rust_file.write_text(code)

        if compile:  # pragma: nocover
            command = ["cargo", "build", "--quiet", "--manifest-path", str(cargo_toml)]
            exit_code = subprocess.run(command).returncode

            if exit_code != 0:
                return exit_code

            binary_file = self.transpiled_rust_root / "target/debug/aaa-stdlib-user"
            binary_file.rename(self.generated_binary_file)

        if run_binary:  # pragma: nocover
            command = [str(self.generated_binary_file)] + args
            return subprocess.run(command).returncode

        return 0

    def _indent(self, line: str) -> str:
        indentation = "    " * self.indent_level
        return indentation + line

    def _generate_rust_file(self) -> str:
        content = "#![allow(unused_imports)]\n"
        content += "#![allow(unused_mut)]\n"
        content += "#![allow(unused_variables)]\n"
        content += "#![allow(dead_code)]\n"
        content += "\n"
        content += "use aaa_stdlib::map::Map;\n"
        content += "use aaa_stdlib::stack::Stack;\n"
        content += "use aaa_stdlib::set::Set;\n"
        content += "use aaa_stdlib::var::{Enum, Struct, Variable};\n"
        content += "use aaa_stdlib::vector::Vector;\n"
        content += "use regex::Regex;\n"
        content += "use std::cell::RefCell;\n"
        content += "use std::collections::HashMap;\n"
        content += "use std::process;\n"
        content += "use std::rc::Rc;\n"

        content += "\n"

        for type in self.types.values():
            if type.is_enum():
                content += self._generate_rust_enum_new_func(type)
            else:
                content += self._generate_rust_struct_new_func(type)

        for function in self.functions.values():
            if function.position.file == self.builtins_path:
                continue
            content += self._generate_rust_function(function)

        content += self._generate_rust_main_function()

        return content

    def _generate_rust_main_function(self) -> str:
        main_func = self.functions[(self.entrypoint, "main")]
        main_func_name = self._generate_rust_function_name(main_func)

        argv_used = len(main_func.arguments) != 0
        exit_code_returned = (
            isinstance(main_func.return_types, list)
            and len(main_func.return_types) != 0
        )

        code = "fn main() {\n"
        self.indent_level += 1

        if argv_used:
            code += self._indent("let mut stack = Stack::from_argv();\n")
        else:
            code += self._indent("let mut stack = Stack::new();\n")

        code += self._indent(f"{main_func_name}(&mut stack);\n")

        if exit_code_returned:
            code += self._indent("stack.exit();\n")

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

        # TODO #37 Use modules in generated code so we don't have to hash at all

        # hash file and name to prevent naming collisions
        hash_input = f"{function.position.file} {function.name}"
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]

        if function.is_enum_ctor:
            return f"user_enum_func_{hash}"
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
        variant_type, variant_id = enum_type.enum_fields[function.func_name]

        content = f"// Generated for: {function.position.file} enum {function.struct_name}, variant {function.func_name}\n"
        content += f"fn {func_name}(stack: &mut Stack) {{\n"

        self.indent_level += 1

        if variant_type:
            content += self._indent("let value = stack.pop();\n")

        content += self._indent("let enum_ = Enum {\n")
        self.indent_level += 1
        content += self._indent(f'type_name: String::from("{function.struct_name}"),\n')
        content += self._indent(f"discriminant: {variant_id},\n")

        if variant_type:
            content += self._indent("value,\n")
        else:
            content += self._indent("value: Variable::None,\n")

        self.indent_level -= 1
        content += self._indent("};\n")

        content += self._indent("stack.push_enum(enum_);\n")

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
                content += self._indent(f"let mut var_{arg.name} = stack.pop();\n")
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
        code = self._indent(f"match stack.get_enum_discriminant() {{\n")
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
            code += self._indent("_ => {}\n")

        self.indent_level -= 1

        code += self._indent("}\n")

        return code

    def _generate_rust_case_block_code(self, case_block: CaseBlock) -> str:
        enum_type = case_block.enum_type
        variant_type, variant_id = enum_type.enum_fields[case_block.variant_name]

        code = self._indent(
            f"{variant_id} => {{ // {enum_type.name}:{case_block.variant_name}\n"
        )
        self.indent_level += 1

        if variant_type is None:
            code += self._indent("stack.drop();\n")

        code += self._generate_rust_function_body(case_block.body)
        self.indent_level -= 1
        code += self._indent("}\n")

        return code

    def _generate_rust_default_block_code(self, default_block: DefaultBlock) -> str:
        code = self._indent("_ => {\n")
        self.indent_level += 1
        code += self._indent("stack.drop();\n")
        code += self._generate_rust_function_body(default_block.body)
        self.indent_level -= 1
        code += self._indent("}\n")

        return code

    def _generate_rust_return(self, return_: Return) -> str:
        return self._indent("return;\n")

    def _generate_rust_string_literal(self, string_literal: StringLiteral) -> str:
        string_value = repr(string_literal.value)[1:-1].replace('"', '\\"')
        return self._indent(f'stack.push_str("{string_value}");\n')

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
            if called.name in ["assert", "todo", "unreachable"]:
                position = call_func.position
                return self._indent(
                    f'{rust_func_name}("{position.file}", {position.line}, {position.column});\n'
                )
            return self._indent(f"{rust_func_name}();\n")

        return self._indent(f"{rust_func_name}(stack);\n")

    def _generate_rust_call_type_code(self, call_type: CallType) -> str:
        var_type = call_type.var_type
        zero_expr = self._generate_rust_variable_zero_expression(var_type)
        return self._indent(f"stack.push({zero_expr});\n")

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

    def _generate_rust_enum_name(self, type: Type) -> str:
        hash_input = f"{type.position.file} {type.name}"
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]
        return f"user_enum_{hash}"

    def _generate_rust_struct_name(self, type: Type) -> str:
        hash_input = f"{type.position.file} {type.name}"
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]
        return f"user_struct_{hash}"

    def _generate_rust_enum_new_func(self, type: Type) -> str:
        rust_enum_name = self._generate_rust_enum_name(type)

        code = f"// Generated for: {type.position.file} {type.name}, zero-value\n"
        code += f"fn {rust_enum_name}_new() -> Enum {{\n"

        zero_variant_var_type: Optional[VariableType] = None

        for variant_type, variant_id in type.enum_fields.values():
            if variant_id == 0:
                zero_variant_var_type = variant_type

        if zero_variant_var_type:
            zero_value_expr = self._generate_rust_variable_zero_expression(
                zero_variant_var_type
            )
        else:
            zero_value_expr = "Variable::None"

        self.indent_level += 1

        code += self._indent("Enum {\n")
        self.indent_level += 1

        code += self._indent(f'type_name: String::from("{type.name}"),\n')
        code += self._indent("discriminant: 0,\n")
        code += self._indent(f"value: {zero_value_expr},\n")

        self.indent_level -= 1
        code += self._indent("}\n")

        self.indent_level -= 1
        code += "}\n\n"

        return code

    def _generate_rust_variable_zero_expression(self, var_type: VariableType) -> str:
        if var_type.name == "int":
            return "Variable::Integer(0)"
        elif var_type.name == "bool":
            return "Variable::Boolean(false)"
        elif var_type.name == "str":
            return 'Variable::String(Rc::new(RefCell::new(String::from(""))))'
        elif var_type.name == "vec":
            return "Variable::Vector(Rc::new(RefCell::new(Vector::new())))"
        elif var_type.name == "map":
            return "Variable::Map(Rc::new(RefCell::new(Map::new())))"
        elif var_type.name == "set":
            return "Variable::Set(Rc::new(RefCell::new(Set::new())))"
        elif var_type.name == "regex":
            return 'Variable::Regex(Rc::new(RefCell::new(Regex::new("$.^").unwrap())))'
        elif var_type.type.is_enum():
            rust_enum_name = self._generate_rust_enum_name(var_type.type)
            return f"Variable::Enum(Rc::new(RefCell::new({rust_enum_name}_new())))"
        else:
            rust_struct_name = self._generate_rust_struct_name(var_type.type)
            return f"Variable::Struct(Rc::new(RefCell::new({rust_struct_name}_new())))"

    def _generate_rust_struct_new_func(self, type: Type) -> str:
        if type.position.file == self.builtins_path and not type.fields:
            return ""

        rust_struct_name = self._generate_rust_struct_name(type)

        code = f"// Generated for: {type.position.file} {type.name}\n"
        code += f"fn {rust_struct_name}_new() -> Struct {{\n"

        self.indent_level += 1
        code += self._indent(f'let type_name = String::from("{type.name}");\n')
        code += self._indent("let values = HashMap::from([\n")

        self.indent_level += 1

        for field_name, field_type in type.fields.items():
            zero_expr = self._generate_rust_variable_zero_expression(field_type)
            code += self._indent(f'(String::from("{field_name}"), {zero_expr}),\n')

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

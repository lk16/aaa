import subprocess
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional, Tuple

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
from aaa.transpiler.code import Code
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
        self.functions = cross_referencer_output.functions
        self.builtins_path = cross_referencer_output.builtins_path
        self.entrypoint = cross_referencer_output.entrypoint
        self.position_stacks = type_checker_output.position_stacks
        self.verbose = verbose

        self.transpiled_rust_root = Path("/tmp/transpiled")

        self.generated_binary_file = (
            generated_binary_file
            or Path(NamedTemporaryFile(delete=False).name).resolve()
        )

        self.user_structs: Dict[Tuple[Path, str], Type] = {}
        self.user_enums: Dict[Tuple[Path, str], Type] = {}

        for key, type in cross_referencer_output.types.items():
            if type.position.file == self.builtins_path:
                continue
            if type.is_enum():
                self.user_enums[key] = type
            else:
                self.user_structs[key] = type

    def run(self, compile: bool, run_binary: bool, args: List[str]) -> int:
        generated_rust_file = self.transpiled_rust_root / "src/main.rs"
        cargo_toml = (self.transpiled_rust_root / "Cargo.toml").resolve()
        stdlib_impl_path = (Path(__file__).parent / "../../aaa-stdlib").resolve()

        generated_rust_file.parent.mkdir(parents=True, exist_ok=True)

        cargo_toml.write_text(
            CARGO_TOML_TEMPLATE.format(stdlib_impl_path=stdlib_impl_path)
        )

        code = self._generate_file()

        generated_rust_file.write_text(code.get())

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

    def _generate_file(self) -> Code:
        code = self._generate_header_comment()
        code.add(self._generate_warning_silencing_macros())
        code.add(self._generate_imports())

        code.add(self._generate_UserTypeEnum())
        code.add(self._generate_UserTypeEnum_impl())
        code.add(self._generate_UserTypeEnum_UserType_impl())
        code.add(self._generate_UserTypeEnum_Display_impl())
        code.add(self._generate_UserTypeEnum_Debug_impl())

        for type in self.user_enums.values():
            code.add(self._generate_enum_new_func(type))

        for type in self.user_structs.values():
            code.add(self._generate_struct(type))
            code.add(self._generate_struct_new_func(type))
            code.add(self._generate_struct_UserType_impl(type))
            code.add(self._generate_struct_Display_impl(type))
            code.add(self._generate_struct_Hash_impl(type))
            code.add(self._generate_struct_PartialEq_impl(type))

        for function in self.functions.values():
            code.add(self._generate_function(function))

        code.add(self._generate_main_function())

        return code

    def _generate_header_comment(self) -> Code:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        code = Code("// #######################################################")
        code.add("// # This file is machine generated. Do not edit.        #")
        code.add(f"// # Generated by Aaa Transpiler on {now}. #")
        code.add("// # https://github.com/lk16/aaa                         #")
        code.add("// #######################################################")
        code.add("")
        return code

    def _generate_warning_silencing_macros(self) -> Code:
        code = Code("#![allow(unused_imports)]")
        code.add("#![allow(unused_mut)]")
        code.add("#![allow(unused_variables)]")
        code.add("#![allow(dead_code)]")
        code.add("#![allow(non_snake_case)]")
        code.add("")
        return code

    def _generate_imports(self) -> Code:
        code = Code("use aaa_stdlib::map::Map;")
        code.add("use aaa_stdlib::stack::Stack;")
        code.add("use aaa_stdlib::set::Set;")
        code.add("use aaa_stdlib::var::{Enum, UserType, Variable};")
        code.add("use aaa_stdlib::vector::Vector;")
        code.add("use regex::Regex;")
        code.add("use std::cell::RefCell;")
        code.add("use std::collections::HashMap;")
        code.add("use std::fmt::{Debug, Display, Formatter, Result};")
        code.add("use std::hash::Hash;")
        code.add("use std::process;")
        code.add("use std::rc::Rc;")
        code.add("")
        return code

    def _generate_main_function(self) -> Code:
        main_func = self.functions[(self.entrypoint, "main")]
        main_func_name = self._generate_function_name(main_func)

        argv_used = len(main_func.arguments) != 0
        exit_code_returned = (
            isinstance(main_func.return_types, list)
            and len(main_func.return_types) != 0
        )

        code = Code()
        code.add("fn main() {", r=1)

        if argv_used:
            code.add("let mut stack:Stack<UserTypeEnum> = Stack::from_argv();")
        else:
            code.add("let mut stack: Stack<UserTypeEnum> = Stack::new();")

        code.add(f"{main_func_name}(&mut stack);")

        if exit_code_returned:
            code.add("stack.exit();")

        code.add("}", l=1)

        return code

    def _generate_builtin_function_name(self, function: Function) -> str:
        return self._generate_builtin_function_name_from_str(function.name)

    def _generate_builtin_function_name_from_str(self, name: str) -> str:
        if name in AAA_RUST_BUILTIN_FUNCS:
            return AAA_RUST_BUILTIN_FUNCS[name]

        return name.replace(":", "_")

    def _generate_function_name(self, function: Function) -> str:
        if function.position.file == self.builtins_path:
            return "stack." + self._generate_builtin_function_name(function)

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

    def _generate_enum_ctor_function(self, function: Function) -> Code:
        func_name = self._generate_function_name(function)

        enum_type_key = (function.position.file, function.struct_name)
        enum_type = self.user_enums[enum_type_key]
        associated_data, variant_id = enum_type.enum_fields[function.func_name]

        code = Code()
        code.add(
            f"// Generated for: {function.position.file} enum {function.struct_name}, variant {function.func_name}"
        )
        code.add(f"fn {func_name}(stack: &mut Stack<UserTypeEnum>) {{", r=1)
        code.add("let mut values = vec![];")

        for _ in associated_data:
            code.add("values.push(stack.pop());")

        code.add("values.reverse();")
        code.add("let enum_ = Enum {", r=1)
        code.add(f'type_name: String::from("{function.struct_name}"),')
        code.add(f"discriminant: {variant_id},")
        code.add("values,")
        code.add("};", l=1)
        code.add("stack.push_enum(enum_);")
        code.add("}", l=1)
        code.add("")

        return code

    def _generate_function(self, function: Function) -> Code:
        if function.position.file == self.builtins_path:
            return Code()

        if function.is_enum_ctor:
            return self._generate_enum_ctor_function(function)

        assert function.body

        func_name = self._generate_function_name(function)

        code = Code(f"// Generated from: {function.position.file} {function.name}")
        code.add(f"fn {func_name}(stack: &mut Stack<UserTypeEnum>) {{", r=1)

        if function.arguments:
            code.add("// load arguments")
            for arg in reversed(function.arguments):
                code.add(f"let mut var_{arg.name} = stack.pop();")
            code.add("")

        code.add(self._generate_function_body(function.body))

        code.add("}", l=1)
        code.add("")

        return code

    def _generate_function_body(self, function_body: FunctionBody) -> Code:
        code = Code()

        for item in function_body.items:
            code.add(self._generate_function_body_item(item))

        return code

    def _generate_function_body_item(self, item: FunctionBodyItem) -> Code:
        if isinstance(item, IntegerLiteral):
            return Code(f"stack.push_int({item.value});")
        elif isinstance(item, StringLiteral):
            return self._generate_string_literal(item)
        elif isinstance(item, BooleanLiteral):
            bool_value = "true"
            if not item.value:
                bool_value = "false"
            return Code(f"stack.push_bool({bool_value});")
        elif isinstance(item, WhileLoop):
            return self._generate_while_loop(item)
        elif isinstance(item, ForeachLoop):
            return self._generate_foreach_loop(item)
        elif isinstance(item, CallFunction):
            return self._generate_call_function_code(item)
        elif isinstance(item, CallType):
            return self._generate_call_type_code(item)
        elif isinstance(item, Branch):
            return self._generate_branch(item)
        elif isinstance(item, StructFieldQuery):
            return self._generate_field_query_code(item)
        elif isinstance(item, StructFieldUpdate):
            return self._generate_field_update_code(item)
        elif isinstance(item, UseBlock):
            return self._generate_use_block_code(item)
        elif isinstance(item, CallVariable):
            return self._generate_call_variable_code(item)
        elif isinstance(item, Assignment):
            return self._generate_assignment_code(item)
        elif isinstance(item, Return):
            return self._generate_return(item)
        elif isinstance(item, MatchBlock):
            return self._generate_match_block_code(item)
        else:  # pragma: nocover
            assert False

    def _generate_field_query_code(self, field_query: StructFieldQuery) -> Code:
        field_name = field_query.field_name.value

        position_stack = self.position_stacks[field_query.position]

        assert not isinstance(position_stack, Never)

        struct_type = position_stack[-1].type
        rust_struct_name = self._generate_struct_name(struct_type)

        field_type = struct_type.fields[field_name].type

        code = Code("{", r=1)
        code.add("let popped = stack.pop_user_type();")
        code.add("let borrowed = (*popped).borrow();")

        if field_type.name == "int":
            code.add(f"stack.push_int(borrowed.get_{rust_struct_name}().{field_name});")
        elif field_type.name == "bool":
            code.add(
                f"stack.push_bool(borrowed.get_{rust_struct_name}().{field_name});"
            )
        elif field_type.name == "str":
            code.add("{", r=1)
            code.add(
                f"let str_rc = borrowed.get_{rust_struct_name}().{field_name}.clone();"
            )
            code.add(f"stack.push(Variable::String(str_rc));")
            code.add("}", l=1)
        elif field_type.name == "vec":
            code.add("{", r=1)
            code.add(
                f"let vec_rc = borrowed.get_{rust_struct_name}().{field_name}.clone();"
            )
            code.add(f"stack.push(Variable::Vector(vec_rc));")
            code.add("}", l=1)
        elif field_type.name == "set":
            code.add("{", r=1)
            code.add(
                f"let set_rc = borrowed.get_{rust_struct_name}().{field_name}.clone();"
            )
            code.add(f"stack.push(Variable::Set(set_rc));")
            code.add("}", l=1)
        elif field_type.name == "map":
            code.add("{", r=1)
            code.add(
                f"let map_rc = borrowed.get_{rust_struct_name}().{field_name}.clone();"
            )
            code.add(f"stack.push(Variable::Map(map_rc));")
            code.add("}", l=1)
        elif field_type.name == "regex":
            code.add("{", r=1)
            code.add(
                f"let regex_rc = borrowed.get_{rust_struct_name}().{field_name}.clone();"
            )
            code.add(f"stack.push(Variable::Regex(regex_rc));")
            code.add("}", l=1)
        elif field_type.is_enum():
            code.add("{", r=1)
            code.add(
                f"let enum_rc = borrowed.get_{rust_struct_name}().{field_name}.clone();"
            )
            code.add(f"stack.push(Variable::Enum(enum_rc));")
            code.add("}", l=1)
        else:
            code.add("{", r=1)
            code.add(
                f"let struct_rc = borrowed.get_{rust_struct_name}().{field_name}.clone();"
            )
            code.add(f"stack.push(Variable::UserType(struct_rc));")
            code.add("}", l=1)

        code.add("}", l=1)
        return code

    def _generate_field_update_code(self, field_update: StructFieldUpdate) -> Code:
        field_name = field_update.field_name.value

        _ = field_name

        return Code("todo!();")  # TODO

    def _generate_match_block_code(self, match_block: MatchBlock) -> Code:
        code = Code("match stack.get_enum_discriminant() {", r=1)

        has_default = False

        for block in match_block.blocks:
            if isinstance(block, CaseBlock):
                code.add(self._generate_case_block_code(block))
            elif isinstance(block, DefaultBlock):
                has_default = True
                code.add(self._generate_default_block_code(block))
            else:  # pragma: nocover
                assert False

        if not has_default:
            code.add("_ => {}")

        code.add("}", l=1)

        return code

    def _generate_case_block_code(self, case_block: CaseBlock) -> Code:
        enum_type = case_block.enum_type
        variant_id = enum_type.enum_fields[case_block.variant_name][1]

        code = Code(
            f"{variant_id} => {{ // {enum_type.name}:{case_block.variant_name}", r=1
        )
        code.add("stack.push_enum_assiciated_data();")

        for var in reversed(case_block.variables):
            code.add(f"let mut var_{var.name} = stack.pop();")

        code.add(self._generate_function_body(case_block.body))

        code.add("}", l=1)

        return code

    def _generate_default_block_code(self, default_block: DefaultBlock) -> Code:
        code = Code("_ => {", r=1)
        code.add("stack.drop();")
        code.add(self._generate_function_body(default_block.body))
        code.add("}", l=1)

        return code

    def _generate_return(self, return_: Return) -> Code:
        return Code("return;")

    def _generate_string_literal(self, string_literal: StringLiteral) -> Code:
        string_value = repr(string_literal.value)[1:-1].replace('"', '\\"')
        return Code(f'stack.push_str("{string_value}");')

    def _generate_while_loop(self, while_loop: WhileLoop) -> Code:

        code = Code("loop {", r=1)
        code.add(self._generate_function_body(while_loop.condition))
        code.add("if !stack.pop_bool() {", r=1)
        code.add("break;")
        code.add("}", l=1)
        code.add(self._generate_function_body(while_loop.body))
        code.add("}", l=1)
        return code

    def _generate_foreach_loop(self, foreach_loop: ForeachLoop) -> Code:
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

        iter = self._generate_function_name(iter_func)
        next = self._generate_function_name(next_func)
        break_drop_count = len(next_func.return_types)

        code = Code(f"stack.dup();")

        if iter_func.position.file == self.builtins_path:
            code.add(f"{iter}();")
        else:
            code.add(f"{iter}(stack);")

        code.add("loop {", r=1)

        code.add(f"stack.dup();")
        if iter_func.position.file == self.builtins_path:
            code.add(f"{next}();")
        else:
            code.add(f"{next}(stack);")

        code.add("if !stack.pop_bool() {", r=1)

        for _ in range(break_drop_count):
            code.add("stack.drop();")

        code.add("break;")

        code.add("}", l=1)

        code.add(self._generate_function_body(foreach_loop.body))

        code.add("}", l=1)
        code.add("stack.drop();")

        return code

    def _generate_call_function_code(self, call_func: CallFunction) -> Code:
        called = call_func.function
        rust_func_name = self._generate_function_name(called)

        if called.position.file == self.builtins_path:
            if called.name in ["assert", "todo", "unreachable"]:
                position = call_func.position
                return Code(
                    f'{rust_func_name}("{position.file}", {position.line}, {position.column});'
                )
            return Code(f"{rust_func_name}();")

        return Code(f"{rust_func_name}(stack);")

    def _generate_call_type_code(self, call_type: CallType) -> Code:
        var_type = call_type.var_type
        zero_expr = self._generate_variable_zero_expression(var_type)
        return Code(f"stack.push({zero_expr});")

    def _generate_branch(self, branch: Branch) -> Code:
        code = self._generate_function_body(branch.condition)

        code.add("if stack.pop_bool() {", r=1)
        code.add(self._generate_function_body(branch.if_body))

        if branch.else_body:
            code.add("} else {", l=1, r=1)
            code.add(self._generate_function_body(branch.else_body))

        code.add("}", l=1)

        return code

    def _generate_enum_name(self, type: Type) -> str:
        hash_input = f"{type.position.file} {type.name}"
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]
        return f"user_enum_{hash}"

    def _generate_struct_name(self, type: Type) -> str:
        hash_input = f"{type.position.file} {type.name}"
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]
        return f"UserStruct{hash}"

    def _generate_enum_new_func(self, type: Type) -> Code:
        rust_enum_name = self._generate_enum_name(type)

        code = Code(f"// Generated for: {type.position.file} {type.name}, zero-value")
        code.add(f"fn {rust_enum_name}_new() -> Enum<UserTypeEnum> {{", r=1)

        zero_variant_var_types: List[VariableType] = []

        for variant_type, variant_id in type.enum_fields.values():
            if variant_id == 0:
                zero_variant_var_types = variant_type

        zero_value_expressions = [
            self._generate_variable_zero_expression(zero_variant_var_type)
            for zero_variant_var_type in zero_variant_var_types
        ]

        code.add("Enum {", r=1)
        code.add(f'type_name: String::from("{type.name}"),')
        code.add("discriminant: 0,")
        code.add("values: vec![" + ", ".join(zero_value_expressions) + "],")
        code.add("}", l=1)
        code.add("}", l=1)
        code.add("")

        return code

    def _generate_struct_field_zero_expression(self, var_type: VariableType) -> str:
        if var_type.name == "int":
            return "0"
        elif var_type.name == "bool":
            return "false"
        elif var_type.name == "str":
            return 'Rc::new(RefCell::new(String::from("")))'
        elif var_type.name == "vec":
            return "Rc::new(RefCell::new(Vector::new()))"
        elif var_type.name == "map":
            return "Rc::new(RefCell::new(Map::new()))"
        elif var_type.name == "set":
            return "Rc::new(RefCell::new(Set::new()))"
        elif var_type.name == "regex":
            return 'Rc::new(RefCell::new(Regex::new("$.^").unwrap()))'
        elif var_type.type.is_enum():
            rust_enum_name = self._generate_enum_name(var_type.type)
            return f"Rc::new(RefCell::new({rust_enum_name}_new()))"
        else:
            rust_struct_name = self._generate_struct_name(var_type.type)
            return f"Rc::new(RefCell::new({rust_struct_name}::new()))"

    def _generate_variable_zero_expression(self, var_type: VariableType) -> str:
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
            rust_enum_name = self._generate_enum_name(var_type.type)
            return f"Variable::Enum(Rc::new(RefCell::new({rust_enum_name}_new())))"
        else:
            rust_struct_name = self._generate_struct_name(var_type.type)
            return (
                "Variable::UserType(Rc::new(RefCell::new("
                + f"UserTypeEnum::{rust_struct_name}({rust_struct_name}::new())"
                + ")))"
            )

    def _generate_UserTypeEnum(self) -> Code:
        code = Code("#[derive(Clone, Hash, PartialEq)]")
        code.add("enum UserTypeEnum {", r=1)

        for (file, name), type in self.user_structs.items():
            rust_struct_name = self._generate_struct_name(type)
            code.add(
                f"{rust_struct_name}({rust_struct_name}), // Generated for {file} {name}"
            )

        code.add("}", l=1)
        code.add("")
        return code

    def _generate_UserTypeEnum_impl(self) -> Code:
        code = Code("impl UserTypeEnum {", r=1)

        func_code_list: List[Code] = []

        for type in self.user_structs.values():
            rust_struct_name = self._generate_struct_name(type)

            func_code = Code(
                f"fn get_{rust_struct_name}(&self) -> &{rust_struct_name} {{", r=1
            )
            func_code.add("match self {", r=1)
            func_code.add(f"Self::{rust_struct_name}(v) => v,")
            func_code.add(f"_ => unreachable!(),")  # TODO handle type error
            func_code.add("}", l=1)
            func_code.add("}", l=1)

            func_code_list.append(func_code)

        code.add_joined("", func_code_list)
        code.add("}", l=1)
        code.add("")
        return code

    def _generate_UserTypeEnum_UserType_impl(self) -> Code:
        code = Code("impl UserType for UserTypeEnum {", r=1)
        code.add("fn kind(&self) -> String {", r=1)

        if self.user_structs:
            code.add("match self {", r=1)

            for type in self.user_structs.values():
                rust_struct_name = self._generate_struct_name(type)
                code.add(f"Self::{rust_struct_name}(v) => v.kind(),")

            code.add("}", l=1)
        else:
            code.add("unreachable!();")

        code.add("}", l=1)
        code.add("")

        code.add("fn clone_recursive(&self) -> Self {", r=1)
        code.add("todo!();")  # TODO
        code.add("}", l=1)

        code.add("}", l=1)
        code.add("")
        return code

    def _generate_UserTypeEnum_Debug_impl(self) -> Code:
        code = Code("impl Display for UserTypeEnum {", r=1)
        code.add("fn fmt(&self, f: &mut Formatter<'_>) -> Result {", r=1)

        if self.user_structs:
            code.add("match self {", r=1)

            for type in self.user_structs.values():
                rust_struct_name = self._generate_struct_name(type)
                code.add(f'Self::{rust_struct_name}(v) => write!(f, "{{}}", v),')

            code.add("}", l=1)

        else:
            code.add("unreachable!();")

        code.add("}", l=1)
        code.add("}", l=1)
        code.add("")
        return code

    def _generate_UserTypeEnum_Display_impl(self) -> Code:
        code = Code("impl Debug for UserTypeEnum {", r=1)
        code.add("fn fmt(&self, f: &mut Formatter<'_>) -> Result {", r=1)

        if self.user_structs:
            code.add("match self {", r=1)

            for type in self.user_structs.values():
                rust_struct_name = self._generate_struct_name(type)
                code.add(f'Self::{rust_struct_name}(v) => write!(f, "{{:?}}", v),')

            code.add("}", l=1)
        else:
            code.add("unreachable!();")

        code.add("}", l=1)
        code.add("}", l=1)
        code.add("")
        return code

    def _generate_struct(self, type: Type) -> Code:
        if type.position.file == self.builtins_path:
            return Code()

        rust_struct_name = self._generate_struct_name(type)

        code = Code(f"// Generated for: {type.position.file} {type.name}")
        code.add(f"#[derive(Debug, Clone)]")
        code.add(f"struct {rust_struct_name} {{", r=1)

        for field_name, field_type in type.fields.items():
            rust_field_type = self._generate_struct_field_type(field_type)
            code.add(f"{field_name}: {rust_field_type},")

        code.add("}", l=1)
        code.add("")
        return code

    def _generate_struct_field_type(self, var_type: VariableType) -> str:
        if var_type.name == "int":
            return "isize"
        elif var_type.name == "bool":
            return "bool"
        elif var_type.name == "str":
            return "Rc<RefCell<String>>"
        elif var_type.name == "vec":
            return "Rc<RefCell<Vector<Variable<UserTypeEnum>>>>"
        elif var_type.name == "map":
            return "Rc<RefCell<Map<Variable<UserTypeEnum>, Variable<UserTypeEnum>>>>"
        elif var_type.name == "set":
            return "Rc<RefCell<Set<Variable<UserTypeEnum>>>>"
        elif var_type.name == "regex":
            return "Rc<RefCell<Regex>>"
        elif var_type.type.is_enum():
            return "Rc<RefCell<Enum<UserTypeEnum>>>"
        return "Rc<RefCell<UserTypeEnum>>"

    def _generate_struct_new_func(self, type: Type) -> Code:
        if type.position.file == self.builtins_path and not type.fields:
            return Code()

        rust_struct_name = self._generate_struct_name(type)

        code = Code(f"// Generated for: {type.position.file} {type.name}")
        code.add(f"impl {rust_struct_name} {{", r=1)
        code.add(f"fn new() -> Self {{", r=1)

        code.add("Self {", r=1)

        # TODO simplify and combine with zero value function
        for field_name, field_var_type in type.fields.items():
            field_type = field_var_type.type

            if field_type.name == "int":
                code.add(f"{field_name}: 0,")
            elif field_type.name == "bool":
                code.add(f"{field_name}: false,")
            elif field_type.name == "str":
                code.add(f'{field_name}: Rc::new(RefCell::new(String::from(""))),')
            elif field_type.name == "vec":
                code.add(f"{field_name}: Rc::new(RefCell::new(Vector::new())),")
            elif field_type.name == "set":
                code.add(f"{field_name}: Rc::new(RefCell::new(Set::new())),")
            elif field_type.name == "map":
                code.add(f"{field_name}: Rc::new(RefCell::new(Map::new())),")
            elif field_type.name == "regex":
                code.add(
                    f'{field_name}: Rc::new(RefCell::new(Regex::new("$.^").unwrap())),'
                )
            elif field_type.is_enum():
                rust_enum_name = self._generate_enum_name(field_type)
                code.add(
                    f"{field_name}: Rc::new(RefCell::new({rust_enum_name}_new())),"
                )

            else:
                rust_struct_name = self._generate_struct_name(field_type)
                code.add(
                    f"{field_name}: Rc::new(RefCell::new("
                    + f"UserTypeEnum::{rust_struct_name}({rust_struct_name}::new())"
                    + ")),"
                )

        code.add("}", l=1)
        code.add("}", l=1)
        code.add("}", l=1)
        code.add("")
        return code

    def _generate_struct_UserType_impl(self, type: Type) -> Code:
        if type.position.file == self.builtins_path:
            return Code()

        rust_struct_name = rust_struct_name = self._generate_struct_name(type)

        code = Code(f"impl UserType for {rust_struct_name} {{", r=1)

        code.add("fn kind(&self) -> String {", r=1)
        code.add(f'String::from("{type.name}")')
        code.add("}", l=1)

        code.add("")

        code.add("fn clone_recursive(&self) -> Self {", r=1)
        code.add("todo!();")  # TODO
        code.add("}", l=1)

        code.add("}", l=1)
        code.add("")
        return code

    def _generate_struct_Display_impl(self, type: Type) -> Code:
        if type.position.file == self.builtins_path:
            return Code()

        rust_struct_name = rust_struct_name = self._generate_struct_name(type)

        code = Code(f"impl Display for {rust_struct_name} {{", r=1)

        code.add("fn fmt(&self, f: &mut Formatter<'_>) -> Result {", r=1)

        code.add(f'write!(f, "(struct {type.name})<")?;')

        is_first_field = True

        for field_name, field_var_type in type.fields.items():
            if is_first_field:
                is_first_field = False
            else:
                code.add('write!(f, ", ")?;')

            if field_var_type.type.name in ["int", "bool"]:
                code.add(f'write!(f, "{field_name}: {{}}", self.{field_name})?;')
            else:
                code.add(
                    f'write!(f, "{field_name}: {{:?}}", *self.{field_name}.borrow())?;'
                )

        code.add('write!(f, ">")')

        code.add("}", l=1)

        code.add("}", l=1)
        code.add("")
        return code

    def _generate_struct_Hash_impl(self, type: Type) -> Code:
        if type.position.file == self.builtins_path:
            return Code()

        rust_struct_name = rust_struct_name = self._generate_struct_name(type)

        code = Code(f"impl Hash for {rust_struct_name} {{", r=1)

        code.add("fn hash<H: std::hash::Hasher>(&self, state: &mut H) {", r=1)
        code.add("todo!();")  # TODO
        code.add("}", l=1)

        code.add("}", l=1)
        code.add("")
        return code

    def _generate_struct_PartialEq_impl(self, type: Type) -> Code:
        if type.position.file == self.builtins_path:
            return Code()

        rust_struct_name = rust_struct_name = self._generate_struct_name(type)

        code = Code(f"impl PartialEq for {rust_struct_name} {{", r=1)
        code.add("fn eq(&self, other: &Self) -> bool {", r=1)
        code.add("true")

        for field_name, field_type in type.fields.items():
            if field_type.name == "regex":
                continue

            code.add(f"&& self.{field_name} == other.{field_name}")

        code.add("}", l=1)
        code.add("}", l=1)
        code.add("")
        return code

    def _generate_use_block_code(self, use_block: UseBlock) -> Code:
        code = Code("{", r=1)

        for var in reversed(use_block.variables):
            code.add(f"let mut var_{var.name} = stack.pop();")

        code.add(self._generate_function_body(use_block.body))
        code.add("}", l=1)

        return code

    def _generate_call_variable_code(self, call_var: CallVariable) -> Code:
        name = call_var.name
        return Code(f"stack.push(var_{name}.clone());")

    def _generate_assignment_code(self, assignment: Assignment) -> Code:
        code = self._generate_function_body(assignment.body)

        for var in reversed(assignment.variables):
            code.add(f"stack.assign(&mut var_{var.name});")

        return code

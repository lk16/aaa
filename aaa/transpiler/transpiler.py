from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple, Type

from aaa import Position, create_output_folder
from aaa.cross_referencer.models import (
    Assignment,
    BooleanLiteral,
    Branch,
    CallEnumConstructor,
    CallFunction,
    CallFunctionByPointer,
    CallType,
    CallVariable,
    CaseBlock,
    CrossReferencerOutput,
    DefaultBlock,
    Enum,
    EnumConstructor,
    ForeachLoop,
    Function,
    FunctionBody,
    FunctionBodyItem,
    FunctionPointer,
    GetFunctionPointer,
    IntegerLiteral,
    MatchBlock,
    Never,
    Return,
    StringLiteral,
    Struct,
    StructFieldQuery,
    StructFieldUpdate,
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


VARIABLE_GET_FUNCTIONS = {
    "int": "get_integer",
    "bool": "get_boolean",
    "str": "get_string",
    "vec": "get_vector",
    "set": "get_set",
    "map": "get_map",
    "vec_iter": "get_vector_iterator",
    "map_iter": "get_map_iterator",
    "set_iter": "get_set_iterator",
    "regex": "get_regex",
}


class Transpiler:
    def __init__(
        self,
        *,
        cross_referencer_output: CrossReferencerOutput,
        type_checker_output: TypeCheckerOutput,
        transpiler_root: Optional[Path],
        runtime_type_checks: bool,
        verbose: bool,
    ) -> None:
        self.functions = cross_referencer_output.functions
        self.builtins_path = cross_referencer_output.builtins_path
        self.entrypoint = cross_referencer_output.entrypoint
        self.position_stacks = type_checker_output.position_stacks
        self.transpiler_root = transpiler_root or create_output_folder()

        self.verbose = verbose
        self.runtime_type_checks = runtime_type_checks

        self.structs: Dict[Tuple[Path, str], Struct] = {}
        self.enums: Dict[Tuple[Path, str], Enum] = {}
        self.builtin_type_names: Set[str] = set()

        # Function currently being transpiled
        self.current_function: Optional[Function] = None

        for key, struct in cross_referencer_output.structs.items():
            if struct.position.file == self.builtins_path:
                self.builtin_type_names.add(struct.name)
            else:
                self.structs[key] = struct

        for key, enum in cross_referencer_output.enums.items():
            if enum.position.file == self.builtins_path:
                self.builtin_type_names.add(enum.name)
            else:
                self.enums[key] = enum

    def run(self) -> None:
        transpiled_file = self.transpiler_root / "src/main.rs"
        transpiled_file.parent.mkdir(parents=True, exist_ok=True)

        code = self._generate_file()
        transpiled_file.write_text(code.get())

        if self.verbose:
            print(f"  transpiler | Saving transpiled file as {transpiled_file}")

    def _generate_file(self) -> Code:
        code = self._generate_header_comment()
        code.add(self._generate_warning_silencing_macros())
        code.add(self._generate_imports())

        code.add(self._generate_UserTypeEnum())
        code.add(self._generate_UserTypeEnum_impl())
        code.add(self._generate_UserTypeEnum_UserType_impl())
        code.add(self._generate_UserTypeEnum_Display_impl())
        code.add(self._generate_UserTypeEnum_Debug_impl())

        for enum in self.enums.values():
            code.add(self._generate_enum(enum))
            code.add(self._generate_enum_constructors(enum))
            code.add(self._generate_enum_impl(enum))
            code.add(self._generate_enum_UserType_impl(enum))
            code.add(self._generate_enum_Display_impl(enum))
            code.add(self._generate_enum_Debug_impl(enum))
            code.add(self._generate_enum_Hash_impl(enum))
            code.add(self._generate_enum_PartialEq_impl(enum))

        for struct in self.structs.values():
            code.add(self._generate_struct(struct))
            code.add(self._generate_struct_impl(struct))
            code.add(self._generate_struct_UserType_impl(struct))
            code.add(self._generate_struct_Display_impl(struct))
            code.add(self._generate_struct_Debug_impl(struct))
            code.add(self._generate_struct_Hash_impl(struct))
            code.add(self._generate_struct_PartialEq_impl(struct))

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
        code.add("#![allow(non_camel_case_types)]")
        code.add("")
        return code

    def _generate_imports(self) -> Code:
        code = Code("use aaa_stdlib::map::Map;")
        code.add("use aaa_stdlib::stack::Stack;")
        code.add("use aaa_stdlib::set::{Set, SetValue};")
        code.add("use aaa_stdlib::var::{UserType, Variable};")
        code.add("use aaa_stdlib::vector::{Vector, VectorIterator};")
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
        return f"user_func_{hash}"

    def _generate_enum_constructor_name(self, enum: Enum, variant_name: str) -> str:
        # TODO #37 Use modules in generated code so we don't have to hash at all

        # hash file and name to prevent naming collisions
        hash_input = f"{enum.position.file} {enum.name}:{variant_name}"
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]
        return f"enum_ctor_{hash}"

    def _get_member_function(self, var_type: VariableType, func_name: str) -> Function:
        # NOTE It is required that member funcitions are
        # defined in same file as the type they operate on.
        file = var_type.type.position.file
        name = f"{var_type.name}:{func_name}"
        return self.functions[(file, name)]

    def _generate_function(self, function: Function) -> Code:
        if function.position.file == self.builtins_path:
            return Code()

        assert function.body

        self.current_function = function

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

        self.current_function = None
        return code

    def _generate_function_body(self, function_body: FunctionBody) -> Code:
        code = Code()

        for item in function_body.items:
            code.add(self._generate_runtime_type_checks(item.position))
            code.add(self._generate_function_body_item(item))

        return code

    def _generate_function_body_item(self, item: FunctionBodyItem) -> Code:
        generate_funcs: Dict[Type[FunctionBodyItem], Callable[..., Code]] = {
            Assignment: self._generate_assignment_code,
            BooleanLiteral: self._generate_boolean_literal,
            Branch: self._generate_branch,
            CallEnumConstructor: self._generate_call_enum_constructor_code,
            CallFunction: self._generate_call_function_code,
            CallFunctionByPointer: self._generate_call_by_function_pointer,
            CallType: self._generate_call_type_code,
            CallVariable: self._generate_call_variable_code,
            ForeachLoop: self._generate_foreach_loop,
            FunctionPointer: self._generate_function_pointer_literal,
            GetFunctionPointer: self._generate_get_function_pointer,
            IntegerLiteral: self._generate_integer_literal,
            MatchBlock: self._generate_match_block_code,
            Return: self._generate_return,
            StringLiteral: self._generate_string_literal,
            StructFieldQuery: self._generate_field_query_code,
            StructFieldUpdate: self._generate_field_update_code,
            UseBlock: self._generate_use_block_code,
            WhileLoop: self._generate_while_loop,
        }

        assert set(generate_funcs.keys()) == set(FunctionBodyItem.__args__)  # type: ignore

        return generate_funcs[type(item)](item)

    def _generate_runtime_type_checks(self, position: Position) -> Code:
        if not self.runtime_type_checks:
            return Code()

        function = self.current_function
        assert function

        # Runtime type checking doesn't work for functions with type parameters,
        # because we don't know the types at transpile-time.
        if function.type_params:
            return Code()

        try:
            type_stack = self.position_stacks[position]
        except KeyError:
            # If there is no type stack for this position, one of these is true:
            # - the code is unreachable
            # - there are bugs in generating the `position_stacks` (in TypeChecker)
            # Since we reached a state that should never happen either way, we want to crash.
            return Code(
                "stack.unreachable_with_position(Some(("
                + f'"{position.file}", {position.line}, {position.column}'
                + ")));"
            )

        # We should not get here with unreachable code
        assert not isinstance(type_stack, Never)

        variable_kinds: List[str] = []
        for item in type_stack:
            if isinstance(item, FunctionPointer):
                variable_kinds.append("fn_ptr")
            else:
                variable_kinds.append(item.name)

        return Code(
            "stack.assert_stack_top_types("
            + f'"{position.file}", {position.line}, {position.column}, vec!['
            + ", ".join(f'"{kind}"' for kind in variable_kinds)
            + "]);"
        )

    def _generate_boolean_literal(self, bool_literal: BooleanLiteral) -> Code:
        bool_value = "true"
        if not bool_literal.value:
            bool_value = "false"

        return Code(f"stack.push_bool({bool_value});")

    def _generate_integer_literal(self, int_literal: IntegerLiteral) -> Code:
        return Code(f"stack.push_int({int_literal.value});")

    def _generate_call_by_function_pointer(
        self, call_by_func_ptr: CallFunctionByPointer
    ) -> Code:
        return Code("stack.pop_function_pointer_and_call();")

    def _get_function_pointer_expression(
        self, target: Function | EnumConstructor
    ) -> str:
        if isinstance(target, EnumConstructor):
            return self._generate_enum_constructor_name(
                target.enum, target.variant_name
            )

        if target.position.file == self.builtins_path:
            return "Stack::" + self._generate_builtin_function_name(target)

        return self._generate_function_name(target)

    def _generate_get_function_pointer(self, get_func_ptr: GetFunctionPointer) -> Code:
        ptr_expr = self._get_function_pointer_expression(get_func_ptr.target)
        return Code(f"stack.push_function_pointer({ptr_expr});")

    def _generate_field_query_code(self, field_query: StructFieldQuery) -> Code:
        field_name = field_query.field_name.value

        type_stack = self.position_stacks[field_query.position]

        # This is enforced by the type checker
        assert not isinstance(type_stack, Never)
        stack_top = type_stack[-1]

        # This is enforced by the type checker
        assert isinstance(stack_top, VariableType)
        struct_type = stack_top.type

        # This is enforced by the type checker
        assert isinstance(struct_type, Struct)

        rust_struct_name = self._generate_type_name(struct_type)

        code = Code("{", r=1)
        code.add("let popped = stack.pop_user_type();")
        code.add("let mut borrowed = (*popped).borrow_mut();")

        code.add(f"stack.push(borrowed.get_{rust_struct_name}().{field_name}.clone());")

        code.add("}", l=1)
        return code

    def _generate_field_update_code(self, field_update: StructFieldUpdate) -> Code:
        code = self._generate_function_body(field_update.new_value_expr)
        field_name = field_update.field_name.value

        type_stack = self.position_stacks[field_update.position]

        # This is verified by the type checker
        assert not isinstance(type_stack, Never)
        stack_top = type_stack[-1]

        # This is verified by the type checker
        assert isinstance(stack_top, VariableType)
        struct_type = stack_top.type

        # This is verified by the type checker
        assert isinstance(struct_type, Struct)

        rust_struct_name = self._generate_type_name(struct_type)
        field_name = field_update.field_name.value

        code.add("{", r=1)

        code.add(f"let value = stack.pop();")

        code.add("let popped = stack.pop_user_type();")
        code.add("let mut borrowed = (*popped).borrow_mut();")
        code.add(f"borrowed.get_{rust_struct_name}().{field_name} = value;")
        code.add("}", l=1)
        return code

    def _generate_match_block_code(self, match_block: MatchBlock) -> Code:
        type_stack = self.position_stacks[match_block.position]

        # This is verified by the type checker
        assert not isinstance(type_stack, Never)
        stack_top = type_stack[-1]

        # This is verified by the type checker
        assert isinstance(stack_top, VariableType)
        enum_type = stack_top.type

        assert isinstance(enum_type, Enum)

        rust_enum_name = self._generate_type_name(enum_type)

        match_var = (
            "match_var_" + sha256(str(match_block.position).encode()).hexdigest()[:16]
        )

        code = Code(
            f"let {match_var} = stack.pop_user_type().borrow_mut().get_{rust_enum_name}().clone();"
        )
        code.add(f"match {match_var} {{", r=1)

        has_default = False
        case_blocks = 0

        for block in match_block.blocks:
            if isinstance(block, CaseBlock):
                case_blocks += 1
                code.add(self._generate_case_block_code(block))
            else:
                assert isinstance(block, DefaultBlock)
                has_default = True
                code.add(self._generate_default_block_code(block))

        if not has_default and case_blocks != len(enum_type.variants):
            code.add("_ => {}")

        code.add("}", l=1)

        return code

    def _generate_case_block_body_with_variables(
        self, case_block: CaseBlock, case_var_prefix: str
    ) -> Code:
        code = Code()

        enum = case_block.enum_type
        variant_name = case_block.variant_name
        associated_data = enum.variants[variant_name]

        for i, (_, var) in enumerate(
            zip(associated_data, case_block.variables, strict=True)
        ):
            arg = f"{case_var_prefix}_{i}"
            code.add(f"let mut var_{var.name}: Variable<UserTypeEnum> = {arg};")

        return code

    def _generate_case_block_body_without_variables(
        self, case_block: CaseBlock, case_var_prefix: str
    ) -> Code:
        code = Code()

        enum = case_block.enum_type
        variant_name = case_block.variant_name
        associated_data = enum.variants[variant_name]

        for i, item in enumerate(associated_data):
            arg = f"{case_var_prefix}_{i}"
            code.add(f"stack.push({arg});")

        return code

    def _generate_case_block_code(self, case_block: CaseBlock) -> Code:
        enum = case_block.enum_type
        variant_name = case_block.variant_name
        associated_data = enum.variants[variant_name]

        rust_enum_name = self._generate_type_name(enum)

        assert len(case_block.variables) in [0, len(associated_data)]

        # NOTE we add the hash of location to prevent collisions with nested case blocks
        case_var_prefix = (
            "case_var_" + sha256(str(case_block.position).encode()).hexdigest()[:16]
        )

        line = f"{rust_enum_name}::variant_{variant_name}("
        line += ", ".join(f"{case_var_prefix}_{i}" for i in range(len(associated_data)))
        line += ") => {"

        code = Code(line, r=1)
        if case_block.variables:
            code.add(
                self._generate_case_block_body_with_variables(
                    case_block, case_var_prefix
                )
            )
        else:
            code.add(
                self._generate_case_block_body_without_variables(
                    case_block, case_var_prefix
                )
            )

        code.add(self._generate_function_body(case_block.body))
        code.add("},", l=1)

        return code

    def _generate_default_block_code(self, default_block: DefaultBlock) -> Code:
        code = Code("_ => {", r=1)
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
        """

        # If any of these next two lines fail, TypeChecker is broken.
        stack = self.position_stacks[foreach_loop.position]

        # This is enforced by the type checker
        assert not isinstance(stack, Never)
        iterable_type = stack[-1]

        # This is enforced by the type checker
        assert isinstance(iterable_type, VariableType)

        if iterable_type.is_const:
            iter_func = self._get_member_function(iterable_type, "const_iter")
        else:
            iter_func = self._get_member_function(iterable_type, "iter")

        assert not isinstance(iter_func.return_types, Never)

        iterator_type = iter_func.return_types[0]

        # This is enforced by the type checker
        assert isinstance(iterator_type, VariableType)

        next_func = self._get_member_function(iterator_type, "next")
        assert not isinstance(next_func.return_types, Never)

        iter = self._generate_function_name(iter_func)
        next = self._generate_function_name(next_func)
        break_drop_count = len(next_func.return_types)

        code = Code()

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

        # drop number of next items - 1 (boolean returned by `next` was popped earlier) + 1 (iterator)
        for _ in range(break_drop_count):
            code.add("stack.drop();")

        code.add("break;")

        code.add("}", l=1)

        code.add(self._generate_function_body(foreach_loop.body))

        code.add("}", l=1)

        return code

    def _generate_call_function_code(self, call_func: CallFunction) -> Code:
        called = call_func.function

        if called.name == "make_const":
            # This function doesn't do anything at runtime, so don't generate any code.
            # In fact it doesn't even exist since #32.
            return Code()

        rust_func_name = self._generate_function_name(called)

        if called.position.file == self.builtins_path:
            if called.name in ["assert", "todo", "unreachable"]:
                position = call_func.position
                rust_func_name = f"stack.{called.name}_with_position"
                return Code(
                    f'{rust_func_name}(Some(("{position.file}", {position.line}, {position.column})));'
                )
            return Code(f"{rust_func_name}();")

        return Code(f"{rust_func_name}(stack);")

    def _generate_call_type_code(self, call_type: CallType) -> Code:
        var_type = call_type.var_type
        zero_expr = self._generate_zero_expression(var_type)
        return Code(f"stack.push({zero_expr});")

    def _generate_call_enum_constructor_code(
        self, call_enum_ctor: CallEnumConstructor
    ) -> Code:
        enum = call_enum_ctor.enum_ctor.enum
        variant_name = call_enum_ctor.enum_ctor.variant_name

        enum_ctor_func_name = self._generate_enum_constructor_name(enum, variant_name)
        return Code(f"{enum_ctor_func_name}(stack);")

    def _generate_branch(self, branch: Branch) -> Code:
        code = self._generate_function_body(branch.condition)

        code.add("if stack.pop_bool() {", r=1)
        code.add(self._generate_function_body(branch.if_body))

        if branch.else_body:
            code.add("} else {", l=1, r=1)
            code.add(self._generate_function_body(branch.else_body))

        code.add("}", l=1)

        return code

    def _generate_type_name(self, type: Enum | Struct) -> str:
        hash_input = f"{type.position.file} {type.name}"
        hash = sha256(hash_input.encode("utf-8")).hexdigest()[:16]

        if isinstance(type, Enum):
            return f"UserEnum{hash}"
        return f"UserStruct{hash}"

    def _generate_enum(self, enum: Enum) -> Code:
        rust_enum_name = self._generate_type_name(enum)

        code = Code(f"// Generated for: {enum.position.file} {enum.name}")
        code.add(f"#[derive(Clone)]")
        code.add(f"enum {rust_enum_name} {{", r=1)

        for variant_name, variant_data in enum.variants.items():
            line = f"variant_{variant_name}("

            line += ", ".join(["Variable<UserTypeEnum>"] * len(variant_data))

            line += "),"
            code.add(line)
        code.add("}", l=1)
        code.add("")
        return code

    def _generate_enum_constructors(self, enum: Enum) -> Code:
        rust_enum_name = self._generate_type_name(enum)

        code = Code()

        for variant_name, associated_data in enum.variants.items():
            enum_ctor_func_name = self._generate_enum_constructor_name(
                enum, variant_name
            )
            code.add(
                f"fn {enum_ctor_func_name}(stack: &mut Stack<UserTypeEnum>) {{", r=1
            )
            for i, _ in reversed(list(enumerate(associated_data))):
                code.add(f"let arg{i} = stack.pop();")

            line = f"let enum_ = {rust_enum_name}::variant_{variant_name}("
            line += ", ".join(f"arg{i}" for i in range(len(associated_data)))
            line += ");"

            code.add(line)
            code.add(f"stack.push_user_type(UserTypeEnum::{rust_enum_name}(enum_));")
            code.add("}", l=1)
            code.add("")
        return code

    def _generate_enum_impl(self, enum: Enum) -> Code:
        rust_enum_name = self._generate_type_name(enum)

        code = Code(f"impl {rust_enum_name} {{", r=1)
        code.add(f"fn new() -> Self {{", r=1)
        code.add(f"Self::variant_{enum.zero_variant}(", r=1)

        for variant_data_item in enum.variants[enum.zero_variant]:
            zero_value = self._generate_zero_expression(variant_data_item)
            code.add(f"{zero_value},")
        code.add(")", l=1)
        code.add("}", l=1)
        code.add("}", l=1)
        code.add("")

        return code

    def _generate_enum_PartialEq_impl(self, enum: Enum) -> Code:
        if enum.position.file == self.builtins_path:
            return Code()

        rust_enum_name = self._generate_type_name(enum)

        code = Code(f"impl PartialEq for {rust_enum_name} {{", r=1)
        code.add("fn eq(&self, other: &Self) -> bool {", r=1)
        code.add("match (self, other) {", r=1)

        for variant_name, associated_data in enum.variants.items():
            line = f"(Self::variant_{variant_name}("
            line += ", ".join([f"lhs_arg{i}" for i in range(len(associated_data))])
            line += f"), Self::variant_{variant_name}("
            line += ", ".join([f"rhs_arg{i}" for i in range(len(associated_data))])
            line += ")) => {"

            code.add(line, r=1)
            code.add("true")

            for i, item in enumerate(associated_data):
                if isinstance(item, FunctionPointer):
                    # Function pointers can't be reliably compared
                    continue

                elif item.type.name == "regex":
                    # Compiled regexes can't be compared
                    continue

                code.add(f"&& lhs_arg{i} == rhs_arg{i}")

            code.add("},", l=1)

        if len(enum.variants) > 1:
            code.add("_ => false,")

        code.add("}", l=1)
        code.add("}", l=1)
        code.add("}", l=1)
        code.add("")
        return code

    def _generate_enum_Hash_impl(self, enum: Enum) -> Code:
        if enum.position.file == self.builtins_path:
            return Code()

        rust_enun_name = self._generate_type_name(enum)

        code = Code(f"impl Hash for {rust_enun_name} {{", r=1)

        code.add("fn hash<H: std::hash::Hasher>(&self, state: &mut H) {", r=1)
        code.add("todo!();")  # TODO #125 Implement hash for structs and enums
        code.add("}", l=1)

        code.add("}", l=1)
        code.add("")
        return code

    def _generate_enum_UserType_impl(self, enum: Enum) -> Code:
        if enum.position.file == self.builtins_path:
            return Code()

        rust_enum_name = self._generate_type_name(enum)

        code = Code(f"impl UserType for {rust_enum_name} {{", r=1)

        code.add("fn kind(&self) -> String {", r=1)
        code.add(f'String::from("{enum.name}")')
        code.add("}", l=1)

        code.add("")

        code.add("fn clone_recursive(&self) -> Self {", r=1)
        code.add("match self {", r=1)

        for variant_name, associated_data in enum.variants.items():
            line = f"Self::variant_{variant_name}("

            line += ", ".join([f"arg{i}" for i in range(len(associated_data))])
            line += ") => {"

            code.add(line, r=1)

            code.add(f"Self::variant_{variant_name}(", r=1)
            for i, _ in enumerate(associated_data):
                code.add(f"arg{i}.clone_recursive(),")
            code.add(")", l=1)

            code.add("},", l=1)

        code.add("}", l=1)
        code.add("}", l=1)
        code.add("}", l=1)
        code.add("")
        return code

    def _generate_enum_Display_impl(self, enum: Enum) -> Code:
        if enum.position.file == self.builtins_path:
            return Code()

        rust_enum_type = self._generate_type_name(enum)

        code = Code(f"impl Display for {rust_enum_type} {{", r=1)

        code.add("fn fmt(&self, f: &mut Formatter<'_>) -> Result {", r=1)
        code.add("match self {", r=1)

        for variant_name, associated_data in enum.variants.items():
            line = f"Self::variant_{variant_name}("
            line += ", ".join([f"arg{i}" for i in range(len(associated_data))])
            line += ") => {"

            code.add(line, r=1)

            code.add(f'write!(f, "{enum.name}:{variant_name}{{{{")?;')

            for offset, item in enumerate(associated_data):
                if offset != 0:
                    code.add('write!(f, ", ")?;')

                code.add(f'write!(f, "{{:?}}", arg{offset})?;')

            code.add('write!(f, "}}")')
            code.add("}", l=1)
        code.add("}", l=1)
        code.add("}", l=1)

        code.add("}", l=1)
        code.add("")
        return code

    def _generate_enum_Debug_impl(self, enum: Enum) -> Code:
        rust_enum_type = self._generate_type_name(enum)

        code = Code(f"impl Debug for {rust_enum_type} {{", r=1)
        code.add("fn fmt(&self, f: &mut Formatter<'_>) -> Result {", r=1)
        code.add(f'write!(f, "{{}}", self)')
        code.add("}", l=1)
        code.add("}", l=1)
        code.add("")
        return code

    def _generate_zero_expression(self, type: VariableType | FunctionPointer) -> str:
        if isinstance(type, FunctionPointer):
            return "Variable::function_pointer_zero_value()"

        if type.name == "int":
            return "Variable::integer_zero_value()"
        elif type.name == "bool":
            return "Variable::boolean_zero_value()"
        elif type.name == "str":
            return "Variable::string_zero_value()"
        elif type.name == "vec":
            return "Variable::vector_zero_value()"
        elif type.name == "map":
            return "Variable::map_zero_value()"
        elif type.name == "set":
            return "Variable::set_zero_value()"
        elif type.name == "regex":
            return "Variable::regex_zero_value()"
        rust_type_name = self._generate_type_name(type.type)
        return f"Variable::UserType(Rc::new(RefCell::new(UserTypeEnum::{rust_type_name}({rust_type_name}::new()))))"

    def _generate_UserTypeEnum(self) -> Code:
        code = Code("#[derive(Clone, Hash, PartialEq)]")
        code.add("enum UserTypeEnum {", r=1)

        for (file, name), struct in self.structs.items():
            rust_struct_name = self._generate_type_name(struct)
            code.add(
                f"{rust_struct_name}({rust_struct_name}), // Generated for {file} {name}"
            )

        for (file, name), enum in self.enums.items():
            rust_struct_name = self._generate_type_name(enum)
            code.add(
                f"{rust_struct_name}({rust_struct_name}), // Generated for {file} {name}"
            )

        code.add("}", l=1)
        code.add("")
        return code

    def _generate_UserTypeEnum_impl(self) -> Code:
        code = Code("impl UserTypeEnum {", r=1)

        func_code_list: List[Code] = []

        user_types = self.structs | self.enums

        for type in user_types.values():
            rust_struct_name = self._generate_type_name(type)

            func_code = Code(
                f"fn get_{rust_struct_name}(&mut self) -> &mut {rust_struct_name} {{",
                r=1,
            )
            func_code.add("match self {", r=1)
            func_code.add(f"Self::{rust_struct_name}(v) => v,")

            if len(user_types) != 1:
                func_code.add(f"_ => unreachable!(),")

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

        user_types = self.structs | self.enums

        if user_types:
            code.add("match self {", r=1)

            for user_type in user_types.values():
                rust_struct_name = self._generate_type_name(user_type)
                code.add(f"Self::{rust_struct_name}(v) => v.kind(),")

            code.add("}", l=1)
        else:
            code.add("unreachable!();")

        code.add("}", l=1)
        code.add("")

        code.add("fn clone_recursive(&self) -> Self {", r=1)

        if user_types:
            code.add("match self {", r=1)

            for user_type in user_types.values():
                rust_struct_name = self._generate_type_name(user_type)
                code.add(
                    f"Self::{rust_struct_name}(v) => Self::{rust_struct_name}(v.clone_recursive()),"
                )

            code.add("}", l=1)
        else:
            code.add("unreachable!();")

        code.add("}", l=1)

        code.add("}", l=1)
        code.add("")
        return code

    def _generate_UserTypeEnum_Debug_impl(self) -> Code:
        code = Code("impl Display for UserTypeEnum {", r=1)
        code.add("fn fmt(&self, f: &mut Formatter<'_>) -> Result {", r=1)

        user_types = self.structs | self.enums

        if user_types:
            code.add("match self {", r=1)

            for type in user_types.values():
                rust_struct_name = self._generate_type_name(type)
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

        user_types = self.structs | self.enums

        if user_types:
            code.add("match self {", r=1)

            for type in user_types.values():
                rust_struct_name = self._generate_type_name(type)
                code.add(f'Self::{rust_struct_name}(v) => write!(f, "{{}}", v),')

            code.add("}", l=1)
        else:
            code.add("unreachable!();")

        code.add("}", l=1)
        code.add("}", l=1)
        code.add("")
        return code

    def _generate_struct(self, struct: Struct) -> Code:
        if struct.position.file == self.builtins_path:
            return Code()

        rust_struct_name = self._generate_type_name(struct)

        code = Code(f"// Generated for: {struct.position.file} {struct.name}")
        code.add(f"#[derive(Clone)]")
        code.add(f"struct {rust_struct_name} {{", r=1)

        for field_name in struct.fields:
            code.add(f"{field_name}: Variable<UserTypeEnum>,")

        code.add("}", l=1)
        code.add("")
        return code

    def _generate_struct_field_type(self, type: VariableType | FunctionPointer) -> str:
        if isinstance(type, FunctionPointer):
            return "fn (&mut Stack<UserTypeEnum>)"
        if type.name == "int":
            return "isize"
        elif type.name == "bool":
            return "bool"
        elif type.name == "str":
            return "Rc<RefCell<String>>"
        elif type.name == "vec":
            return "Rc<RefCell<Vector<Variable<UserTypeEnum>>>>"
        elif type.name == "map":
            return "Rc<RefCell<Map<Variable<UserTypeEnum>, Variable<UserTypeEnum>>>>"
        elif type.name == "set":
            return "Rc<RefCell<Set<Variable<UserTypeEnum>>>>"
        elif type.name == "regex":
            return "Rc<RefCell<Regex>>"
        elif type.name == "vec_iter":
            return "Rc<RefCell<VectorIterator<Variable<UserTypeEnum>>>>"

        if type.name in self.builtin_type_names:
            raise NotImplementedError  # TODO

        return "Rc<RefCell<UserTypeEnum>>"

    def _generate_struct_impl(self, struct: Struct) -> Code:
        if struct.position.file == self.builtins_path and not struct.fields:
            return Code()

        rust_struct_name = self._generate_type_name(struct)

        code = Code(f"// Generated for: {struct.position.file} {struct.name}")
        code.add(f"impl {rust_struct_name} {{", r=1)
        code.add(f"fn new() -> Self {{", r=1)

        code.add("Self {", r=1)

        for field_name, field_var_type in struct.fields.items():
            if isinstance(field_var_type, FunctionPointer):
                code.add(f"{field_name}: Variable::function_pointer_zero_value(),")
                continue

            if field_var_type.name in struct.type_params:
                code.add(f"{field_name}: Variable::None,")
                continue

            if field_var_type.type.name == "int":
                code.add(f"{field_name}: Variable::integer_zero_value(),")
            elif field_var_type.type.name == "bool":
                code.add(f"{field_name}: Variable::boolean_zero_value(),")
            elif field_var_type.type.name == "str":
                code.add(f"{field_name}: Variable::string_zero_value(),")
            elif field_var_type.type.name == "vec":
                code.add(f"{field_name}: Variable::vector_zero_value(),")
            elif field_var_type.type.name == "set":
                code.add(f"{field_name}: Variable::set_zero_value(),")
            elif field_var_type.type.name == "map":
                code.add(f"{field_name}: Variable::map_zero_value(),")
            elif field_var_type.type.name == "regex":
                code.add(f"{field_name}: Variable::regex_zero_value(),")
            elif field_var_type.type.name == "vec_iter":
                code.add(f"{field_name}: Variable::None,")  # TODO this is hacky
            else:
                if field_var_type.type.name in self.builtin_type_names:
                    raise NotImplementedError  # TODO

                rust_struct_name = self._generate_type_name(field_var_type.type)
                code.add(
                    f"{field_name}: Variable::UserType(Rc::new(RefCell::new("
                    + f"UserTypeEnum::{rust_struct_name}({rust_struct_name}::new())"
                    + "))),"
                )

        code.add("}", l=1)
        code.add("}", l=1)
        code.add("}", l=1)
        code.add("")
        return code

    def _generate_clone_recursive_expression(
        self, source_expr: str, type: Struct | Enum
    ) -> Code:
        if type.name in ["bool", "int"]:
            code = Code(source_expr)
        elif type.name == "regex":
            code = Code(f"{source_expr}.clone()")
        elif type.name == "str":
            code = Code(f"let string = (*{source_expr}).borrow().clone();")
            code.add("Rc::new(RefCell::new(string))")
        elif type.name == "vec":
            code = Code("let mut vector = Vector::new();")
            code.add(f"let source = (*{source_expr}).borrow();")
            code.add("for item in source.iter() {", r=1)
            code.add("vector.push(item.clone_recursive())")
            code.add("}", l=1)
            code.add("Rc::new(RefCell::new(vector))")
        elif type.name == "set":
            code = Code("let mut set = Map::new();")
            code.add(f"let source = (*{source_expr}).borrow();")
            code.add("for (item, _) in source.iter() {", r=1)
            code.add("set.insert(item.clone_recursive(), SetValue{});")
            code.add("}", l=1)
            code.add("Rc::new(RefCell::new(set))")
        elif type.name == "map":
            code = Code("let mut map = Map::new();")
            code.add(f"let source = (*{source_expr}).borrow();")
            code.add("for (key, value) in source.iter() {", r=1)
            code.add("map.insert(key.clone_recursive(), value.clone_recursive());")
            code.add("}", l=1)
            code.add("Rc::new(RefCell::new(map))")
        else:
            code = Code(f"let source = (*{source_expr}).borrow();")
            code.add(f"Rc::new(RefCell::new(source.clone_recursive()))")
        return code

    def _generate_struct_UserType_impl(self, struct: Struct) -> Code:
        if struct.position.file == self.builtins_path:
            return Code()

        rust_struct_name = self._generate_type_name(struct)

        code = Code(f"impl UserType for {rust_struct_name} {{", r=1)

        code.add("fn kind(&self) -> String {", r=1)
        code.add(f'String::from("{struct.name}")')
        code.add("}", l=1)

        code.add("")

        code.add("fn clone_recursive(&self) -> Self {", r=1)

        code.add("Self {", r=1)

        for field_name in struct.fields:
            code.add(f"{field_name}: self.{field_name}.clone_recursive(),")

        code.add("}", l=1)

        code.add("}", l=1)

        code.add("}", l=1)
        code.add("")
        return code

    def _generate_struct_Display_impl(self, struct: Struct) -> Code:
        if struct.position.file == self.builtins_path:
            return Code()

        rust_struct_name = self._generate_type_name(struct)

        code = Code(f"impl Display for {rust_struct_name} {{", r=1)

        code.add("fn fmt(&self, f: &mut Formatter<'_>) -> Result {", r=1)

        code.add(f'write!(f, "{struct.name}{{{{")?;')

        for offset, field_name in enumerate(struct.fields):
            if offset != 0:
                code.add('write!(f, ", ")?;')

            code.add(f'write!(f, "{field_name}: {{:?}}", self.{field_name})?;')

        code.add('write!(f, "}}")')

        code.add("}", l=1)

        code.add("}", l=1)
        code.add("")
        return code

    def _generate_struct_Debug_impl(self, struct: Struct) -> Code:
        if struct.position.file == self.builtins_path:
            return Code()

        rust_struct_name = self._generate_type_name(struct)

        code = Code(f"impl Debug for {rust_struct_name} {{", r=1)
        code.add("fn fmt(&self, f: &mut Formatter<'_>) -> Result {", r=1)
        code.add('write!(f, "{}", self)')
        code.add("}", l=1)
        code.add("}", l=1)

        code.add("")
        return code

    def _generate_struct_Hash_impl(self, struct: Struct) -> Code:
        if struct.position.file == self.builtins_path:
            return Code()

        rust_struct_name = self._generate_type_name(struct)

        code = Code(f"impl Hash for {rust_struct_name} {{", r=1)

        code.add("fn hash<H: std::hash::Hasher>(&self, state: &mut H) {", r=1)
        code.add("todo!();")  # TODO #125 Implement hash for structs and enums
        code.add("}", l=1)

        code.add("}", l=1)
        code.add("")
        return code

    def _generate_struct_PartialEq_impl(self, struct: Struct) -> Code:
        if struct.position.file == self.builtins_path:
            return Code()

        rust_struct_name = self._generate_type_name(struct)

        code = Code(f"impl PartialEq for {rust_struct_name} {{", r=1)
        code.add("fn eq(&self, other: &Self) -> bool {", r=1)
        code.add("true")

        for field_name, field_type in struct.fields.items():
            if isinstance(field_type, FunctionPointer):
                continue

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

    def _generate_function_pointer_literal(self, func_ptr: FunctionPointer) -> Code:
        return Code("stack.push_function_pointer(Stack::zero_function_pointer_value);")

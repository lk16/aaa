use chrono::Local;

use crate::{
    common::{
        hash::{hash_key, hash_position},
        traits::HasPosition,
    },
    cross_referencer::types::{
        function_body::{
            Assignment, Boolean, Branch, CallArgument, CallEnum, CallEnumConstructor, CallFunction,
            CallInterfaceFunction, CallLocalVariable, CallStruct, CaseBlock, Char, DefaultBlock,
            FunctionBody, FunctionBodyItem, FunctionType, GetField, GetFunction, Integer, Match,
            ParsedString, Return, SetField, Use, While,
        },
        identifiable::{Enum, Function, Identifiable, ReturnTypes, Struct, Type},
    },
    transpiler::code::Code,
    type_checker::type_checker::{self, InterfaceMapping},
};
use lazy_static::lazy_static;
use std::{cell::RefCell, collections::HashMap, fs, iter::zip, path::PathBuf, rc::Rc};

lazy_static! {
    pub static ref CUSTOM_FUNCTION_NAMES: HashMap<&'static str, &'static str> = {
        let array = [
            ("-", "minus"),
            (".", "print"),
            ("*", "multiply"),
            ("/", "divide"),
            ("%", "modulo"),
            ("+", "plus"),
            ("<", "less"),
            ("<=", "less_equal"),
            ("=", "equals"),
            (">", "greater"),
            (">=", "greater_equal"),
        ];

        HashMap::from(array)
    };
}

lazy_static! {
    pub static ref ZERO_VALUE_FUNCTION_NAMES: HashMap<&'static str, &'static str> = {
        let array = [
            ("int", "Variable::integer_zero_value()"),
            ("bool", "Variable::boolean_zero_value()"),
            ("char", "Variable::character_zero_value()"),
            ("str", "Variable::string_zero_value()"),
            ("vec", "Variable::vector_zero_value()"),
            ("map", "Variable::map_zero_value()"),
            ("set", "Variable::set_zero_value()"),
            ("regex", "Variable::regex_zero_value()"),
            ("Option", "Variable::option_zero_value()"),
            ("Result", "Variable::result_zero_value()"),
        ];

        HashMap::from(array)
    };
}

pub struct Transpiler {
    transpiler_root_path: PathBuf,
    pub structs: HashMap<(PathBuf, String), Rc<RefCell<Struct>>>,
    pub enums: HashMap<(PathBuf, String), Rc<RefCell<Enum>>>,
    pub functions: HashMap<(PathBuf, String), Rc<RefCell<Function>>>,
    pub interface_mapping: HashMap<(String, String), InterfaceMapping>,
    pub main_function: Rc<RefCell<Function>>,
    pub verbose: bool,
}

impl Transpiler {
    pub fn new(
        transpiler_root_path: PathBuf,
        type_checked: type_checker::Output,
        verbose: bool,
    ) -> Self {
        let mut functions = HashMap::new();
        let mut structs = HashMap::new();
        let mut enums = HashMap::new();

        for (key, identifiable) in &type_checked.identifiables {
            if identifiable.is_builtin() {
                continue;
            }

            match identifiable {
                Identifiable::Enum(enum_) => {
                    enums.insert(key.clone(), enum_.clone());
                }
                Identifiable::Struct(struct_) => {
                    structs.insert(key.clone(), struct_.clone());
                }
                Identifiable::Function(function) => {
                    functions.insert(key.clone(), function.clone());
                }
                _ => (),
            }
        }

        Self {
            transpiler_root_path,
            structs,
            enums,
            functions,
            main_function: type_checked.main_function,
            verbose,
            interface_mapping: type_checked.interface_mapping,
        }
    }

    pub fn run(&self) {
        let code = self.generate_file();

        fs::create_dir_all(self.transpiler_root_path.join("src")).unwrap();
        let main_path = self.transpiler_root_path.join("src/main.rs");

        if self.verbose {
            println!("writing to {:?}", main_path);
        }

        fs::write(main_path, code.get()).unwrap();
    }

    fn generate_file(&self) -> Code {
        let mut code = Code::new();

        code.add_code(self.generate_header_comment());
        code.add_code(self.generate_warning_silencing_macros());
        code.add_code(self.generate_imports());

        code.add_code(self.generate_interface_mapping());

        code.add_code(self.generate_UserTypeEnum());

        for enum_ in self.enums.values() {
            let enum_ = &*enum_.borrow();
            code.add_code(self.generate_enum(enum_));
        }

        for struct_ in self.structs.values() {
            let struct_ = &*struct_.borrow();
            code.add_code(self.generate_struct(struct_));
        }

        for function in self.functions.values() {
            let function = &*function.borrow();
            code.add_code(self.generate_function(function));
        }

        code.add_code(self.generate_main_function());

        code
    }

    fn generate_header_comment(&self) -> Code {
        let now = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

        let mut code = Code::new();
        code.add_line("// #######################################################");
        code.add_line("// # This file is machine generated. Do not edit.        #");
        code.add_line(format!("// # Generated by Aaa Transpiler on {}. #", now));
        code.add_line("// # https://github.com/lk16/aaa                         #");
        code.add_line("// #######################################################");
        code.add_line("");

        code
    }

    fn generate_warning_silencing_macros(&self) -> Code {
        let mut code = Code::new();

        code.add_line("#![allow(unused_imports)]");
        code.add_line("#![allow(unused_mut)]");
        code.add_line("#![allow(unused_variables)]");
        code.add_line("#![allow(dead_code)]");
        code.add_line("#![allow(non_snake_case)]");
        code.add_line("#![allow(non_camel_case_types)]");
        code.add_line("");

        code
    }

    fn generate_imports(&self) -> Code {
        let mut code = Code::new();

        code.add_line("use aaa_stdlib::map::Map;");
        code.add_line("use aaa_stdlib::set::{Set, SetValue};");
        code.add_line("use aaa_stdlib::stack::Stack;");
        code.add_line("use aaa_stdlib::var::{UserType, Variable};");
        code.add_line("use aaa_stdlib::vector::Vector;");
        code.add_line("use lazy_static::lazy_static;");
        code.add_line("use regex::Regex;");
        code.add_line("use std::cell::RefCell;");
        code.add_line("use std::collections::HashMap;");
        code.add_line("use std::hash::Hash;");
        code.add_line("use std::process;");
        code.add_line("use std::rc::Rc;");
        code.add_line("use std::sync::Arc;");
        code.add_line("");

        code
    }

    fn generate_interface_mapping(&self) -> Code {
        let mut code = Code::new();

        code.add_line("type InterfaceMapPointer = fn(&mut Stack<UserTypeEnum>);");
        code.add_line("");

        code.add_line("lazy_static! {");
        code.add_line("static ref INTERFACE_MAPPING: Arc<HashMap<(&'static str, &'static str), HashMap<&'static str, InterfaceMapPointer>>> = {");

        code.add_line("let hash_map = HashMap::from([");
        code.indent();

        for ((interface_hash, implementor_hash), interface_mapping) in &self.interface_mapping {
            // TODO put comments in generated files to assist future debugging
            code.add_line(format!(
                "((\"{}\", \"{}\"), HashMap::from([",
                interface_hash, implementor_hash
            ));
            code.indent();

            for (function_name, function) in interface_mapping {
                let function = &*function.borrow();

                let function_ptr_expr = if function.is_builtin {
                    format!("Stack::{}", self.generate_builtin_function_name(function))
                } else {
                    let hash = Self::hash_name(function.position().path, function.name());
                    format!("user_func_{}", hash)
                };

                code.add_line(format!(
                    "(\"{}\", {} as InterfaceMapPointer),",
                    function_name, function_ptr_expr
                ));
            }

            code.unindent();
            code.add_line("])),")
        }

        code.unindent();
        code.add_line("]);");

        code.add_line("Arc::new(hash_map)");

        code.add_line("};");
        code.add_line("}");

        code.add_line("");

        code
    }

    #[allow(non_snake_case)]
    fn generate_UserTypeEnum(&self) -> Code {
        let mut code = Code::new();

        code.add_code(self.generate_UserTypeEnum_definition());
        code.add_code(self.generate_UserTypeEnum_impl());
        code.add_code(self.generate_UserTypeEnum_UserType_impl());

        code
    }

    fn generate_enum(&self, enum_: &Enum) -> Code {
        let mut code = Code::new();

        code.add_code(self.generate_enum_definition(enum_));
        code.add_code(self.generate_enum_constructors(enum_));
        code.add_code(self.generate_enum_impl(enum_));
        code.add_code(self.generate_enum_UserType_impl(enum_));
        code.add_code(self.generate_enum_Hash_impl(enum_));
        code.add_code(self.generate_enum_PartialEq_impl(enum_));

        code
    }

    fn generate_struct(&self, struct_: &Struct) -> Code {
        let mut code = Code::new();

        code.add_code(self.generate_struct_definition(struct_));
        code.add_code(self.generate_struct_impl(struct_));
        code.add_code(self.generate_struct_UserType_impl(struct_));
        code.add_code(self.generate_struct_Hash_impl(struct_));
        code.add_code(self.generate_struct_PartialEq_impl(struct_));

        code
    }

    fn user_type_names(&self) -> Vec<String> {
        let mut names = vec![];

        for struct_ in self.structs.values() {
            let struct_ = &*struct_.borrow();
            let name = self.generate_struct_name(struct_);
            names.push(name);
        }

        for enum_ in self.enums.values() {
            let enum_ = &*enum_.borrow();
            let name = self.generate_enum_name(enum_);
            names.push(name);
        }

        names
    }

    #[allow(non_snake_case)]
    fn generate_UserTypeEnum_definition(&self) -> Code {
        let mut code = Code::new();
        code.add_line("#[derive(Clone, Hash, PartialEq)]");
        code.add_line("pub enum UserTypeEnum {");

        for ((path, name), struct_) in &self.structs {
            let struct_ = &*struct_.borrow();
            let struct_name = self.generate_struct_name(struct_);

            code.add_line(format!("// Generated for {} {}", path.display(), name));
            code.add_line(format!("{}({}),", struct_name, struct_name));
            code.add_line("");
        }

        for ((path, name), enum_) in &self.enums {
            let enum_ = &*enum_.borrow();
            let enum_name = self.generate_enum_name(enum_);

            code.add_line(format!("// Generated for {} {}", path.display(), name));
            code.add_line(format!("{}({}),", enum_name, enum_name));
            code.add_line("");
        }

        code.add_line("}");
        code.add_line("");

        code
    }

    #[allow(non_snake_case)]
    fn generate_UserTypeEnum_impl(&self) -> Code {
        let mut code = Code::new();

        code.add_line("impl UserTypeEnum {");

        let names = self.user_type_names();

        for name in &names {
            code.add_line(format!("fn get_{}(&mut self) -> &mut {} {{", name, name));
            code.add_line("match self {");
            code.add_line(format!("Self::{}(v) => v,", name));

            if names.len() != 1 {
                code.add_line("_ => unreachable!(),");
            }

            code.add_line("}");
            code.add_line("}");
        }

        code.add_line("}");
        code.add_line("");

        code
    }

    #[allow(non_snake_case)]
    fn generate_UserTypeEnum_UserType_impl(&self) -> Code {
        let names = self.user_type_names();

        let mut code = Code::new();
        code.add_line("impl UserType for UserTypeEnum {");

        code.add_line("fn type_id(&self) -> String {");

        if names.is_empty() {
            code.add_line("unreachable!();");
        } else {
            code.add_line("match self {");
            for name in &names {
                code.add_line(format!("Self::{name}(v) => v.type_id(),"));
            }
            code.add_line("}");
        }

        code.add_line("}");

        code.add_line("");

        code.add_line("fn clone_recursive(&self) -> Self {");

        if names.is_empty() {
            code.add_line("unreachable!();");
        } else {
            code.add_line("match self {");
            for name in &names {
                code.add_line(format!(
                    "Self::{name}(v) => Self::{name}(v.clone_recursive()),"
                ));
            }
            code.add_line("}");
        }

        code.add_line("}");

        code.add_line("}");
        code.add_line("");

        code
    }

    fn generate_builtin_function_name(&self, function: &Function) -> String {
        let function_name = function.name();

        if let Some(name) = CUSTOM_FUNCTION_NAMES.get(function_name.as_str()) {
            return name.to_string();
        }

        function_name.replace(":", "_").to_lowercase()
    }

    fn hash_name(path: PathBuf, name: String) -> String {
        hash_key((path, name))
    }

    fn generate_function_name(&self, function: &Function) -> String {
        if function.is_builtin {
            return format!("stack.{}", self.generate_builtin_function_name(function));
        }

        let hash = Self::hash_name(function.position().path, function.name());
        format!("user_func_{}", hash)
    }

    fn generate_struct_name(&self, struct_: &Struct) -> String {
        let hash = Self::hash_name(struct_.position().path.clone(), struct_.name());
        format!("user_type_{}", hash)
    }

    fn generate_enum_name(&self, enum_: &Enum) -> String {
        let hash = Self::hash_name(enum_.position().path.clone(), enum_.name());
        format!("user_type_{}", hash)
    }

    fn generate_main_function(&self) -> Code {
        let main_function = &*self.main_function.borrow();

        let main_func_name = self.generate_function_name(main_function);

        let mut code = Code::new();
        code.add_line("fn main() {");

        code.add_line("let interface_mapping = Arc::clone(&INTERFACE_MAPPING);");

        if main_function.arguments().is_empty() {
            code.add_line("let mut stack: Stack<UserTypeEnum> = Stack::new(interface_mapping);");
        } else {
            code.add_line(
                "let mut stack:Stack<UserTypeEnum> = Stack::from_argv(interface_mapping);",
            );
        }

        code.add_line(format!("{}(&mut stack);", main_func_name));

        let exit_code_returned = match &main_function.signature().return_types {
            ReturnTypes::Never => false,
            ReturnTypes::Sometimes(types) => !types.is_empty(),
        };

        if exit_code_returned {
            code.add_line("stack.exit();")
        }

        code.add_line("}");

        code
    }

    fn generate_function(&self, function: &Function) -> Code {
        let mut code = Code::new();

        let name = self.generate_function_name(function);

        code.add_line(format!(
            "// Generated from: {} {}",
            function.position().path.display(),
            function.name()
        ));
        code.add_line(format!("fn {}(stack: &mut Stack<UserTypeEnum>) {{", name));

        if !function.arguments().is_empty() {
            code.add_line("// load arguments");
            for argument in function.arguments().iter().rev() {
                code.add_line(format!("let mut var_{} = stack.pop();", argument.name));
            }
            code.add_line("");
        }

        code.add_code(self.generate_function_body(function.body()));
        code.add_line("}");
        code.add_line("");

        code
    }

    fn generate_function_body(&self, body: &FunctionBody) -> Code {
        let mut code = Code::new();

        for item in &body.items {
            code.add_code(self.generate_function_body_item(item));
        }

        code
    }

    fn generate_function_body_item(&self, item: &FunctionBodyItem) -> Code {
        use FunctionBodyItem::*;

        match item {
            Assignment(assignment) => self.generate_assignment(assignment),
            Boolean(bool) => self.generate_boolean(bool),
            Branch(branch) => self.generate_branch(branch),
            Call(_) => self.generate_call(),
            CallArgument(call) => self.generate_call_argument(call),
            CallEnum(call) => self.generate_call_enum(call),
            CallEnumConstructor(call) => self.generate_call_enum_constructor(call),
            CallFunction(call) => self.generate_call_function(call),
            CallInterfaceFunction(call) => self.generate_call_interface_function(call),
            CallLocalVariable(call) => self.generate_call_local_variabiable(call),
            CallStruct(call) => self.generate_call_struct(call),
            Char(char) => self.generate_char(char),
            Foreach(_) => unreachable!(), // TODO #243 Support foreach loops
            FunctionType(function_type) => self.generate_function_type(function_type),
            GetField(get_field) => self.generate_get_field(get_field),
            GetFunction(get_function) => self.generate_get_function(get_function),
            Integer(integer) => self.generate_integer(integer),
            Match(match_) => self.generate_match(match_),
            Return(return_) => self.generate_return(return_),
            SetField(set_field) => self.generate_set_field(set_field),
            String(string) => self.generate_string(string),
            Use(use_) => self.generate_use(use_),
            While(while_) => self.generate_while(while_),
        }
    }

    fn generate_string(&self, string: &ParsedString) -> Code {
        Code::from_string(format!("stack.push_str({:?});", string.value))
    }

    fn generate_integer(&self, integer: &Integer) -> Code {
        Code::from_string(format!("stack.push_int({});", integer.value))
    }

    fn generate_char(&self, char: &Char) -> Code {
        Code::from_string(format!("stack.push_char({:?});", char.value))
    }

    fn generate_boolean(&self, bool: &Boolean) -> Code {
        Code::from_string(format!("stack.push_bool({:?});", bool.value))
    }

    fn generate_call_function_with_position(&self, call: &CallFunction) -> Code {
        let function = &*call.function.borrow();
        let name = self.generate_function_name(function);

        let position_expr = format!(
            "Some(({:?}, {}, {}))",
            call.position.path, call.position.line, call.position.column
        );

        Code::from_string(format!("{}_with_position({})", name, position_expr))
    }

    fn generate_call_function(&self, call: &CallFunction) -> Code {
        let function = &*call.function.borrow();

        match function.name().as_str() {
            "assert" | "todo" | "unreachable " => {
                return self.generate_call_function_with_position(call)
            }
            _ => (),
        }

        let name = self.generate_function_name(function);

        if function.is_builtin {
            Code::from_string(format!("{}();", name))
        } else {
            Code::from_string(format!("{}(stack);", name))
        }
    }

    fn generate_branch(&self, branch: &Branch) -> Code {
        let mut code = self.generate_function_body(&branch.condition);

        code.add_line("if stack.pop_bool() {");
        code.add_code(self.generate_function_body(&branch.if_body));

        if let Some(else_body) = &branch.else_body {
            code.add_line("} else {");
            code.add_code(self.generate_function_body(else_body));
        }

        code.add_line("}");

        code
    }

    fn generate_use(&self, use_: &Use) -> Code {
        let mut code = Code::new();

        code.add_line("{");

        for variable in use_.variables.iter().rev() {
            code.add_line(format!(
                "let mut var_{} = stack.pop();",
                variable.name.clone()
            ));
        }

        code.add_code(self.generate_function_body(&use_.body));
        code.add_line("}");

        code
    }

    fn generate_call_local_variabiable(&self, call: &CallLocalVariable) -> Code {
        Code::from_string(format!("stack.push(var_{}.clone());", call.name.clone()))
    }

    fn generate_assignment(&self, assignment: &Assignment) -> Code {
        let mut code = self.generate_function_body(&assignment.body);

        for variable in assignment.variables.iter().rev() {
            code.add_line(format!("stack.assign(&mut var_{});", variable.name.clone()));
        }

        code
    }

    fn generate_call_argument(&self, call: &CallArgument) -> Code {
        Code::from_string(format!("stack.push(var_{}.clone());", call.name.clone()))
    }

    fn generate_while(&self, while_: &While) -> Code {
        let mut code = Code::new();

        code.add_line("loop {");
        code.add_code(self.generate_function_body(&while_.condition));
        code.add_line("if !stack.pop_bool() {");
        code.add_line("break;");
        code.add_line("}");
        code.add_code(self.generate_function_body(&while_.body));
        code.add_line("}");

        code
    }

    fn generate_return(&self, _: &Return) -> Code {
        Code::from_string("return;")
    }

    fn generate_function_type(&self, _: &FunctionType) -> Code {
        Code::from_string("Variable::function_pointer_zero_value()")
    }

    fn generate_struct_zero_expression(&self, struct_: &Struct) -> String {
        self.generate_zero_expression(struct_.position().path, struct_.name())
    }

    fn generate_enum_zero_expression(&self, enum_: &Enum) -> String {
        self.generate_zero_expression(enum_.position().path, enum_.name())
    }

    fn generate_type_zero_expression(&self, type_: &Type) -> String {
        match type_ {
            Type::Struct(struct_) => {
                let struct_ = &*struct_.struct_.borrow();
                self.generate_struct_zero_expression(struct_)
            }
            Type::Enum(enum_) => {
                let enum_ = &*enum_.enum_.borrow();
                self.generate_enum_zero_expression(enum_)
            }
            Type::FunctionPointer(_) => {
                "Variable::FunctionPointer(Stack::zero_function_pointer_value)".to_owned()
            }
            Type::Parameter(_) => "Variable::None".to_owned(),
            Type::Interface(_) => unreachable!(),
        }
    }

    fn generate_zero_expression(&self, path: PathBuf, type_name: String) -> String {
        if let Some(zero_expr) = ZERO_VALUE_FUNCTION_NAMES.get(type_name.as_str()) {
            return zero_expr.to_string();
        }

        let hash = Self::hash_name(path, type_name);
        let user_type = format!("user_type_{}", hash);

        format!(
            "Variable::UserType(Rc::new(RefCell::new(UserTypeEnum::{}({}::new()))))",
            user_type, user_type
        )
    }

    fn generate_call_enum(&self, call: &CallEnum) -> Code {
        let enum_ = &*call.enum_.borrow();
        let zero_expr = self.generate_enum_zero_expression(enum_);

        Code::from_string(format!("stack.push({});", zero_expr))
    }

    fn generate_call_struct(&self, call: &CallStruct) -> Code {
        let struct_ = &*call.struct_.borrow();
        let zero_expr = self.generate_struct_zero_expression(struct_);

        Code::from_string(format!("stack.push({});", zero_expr))
    }

    fn generate_function_pointer_expression(&self, function: &Function) -> String {
        if function.is_builtin {
            format!("Stack::{}", self.generate_builtin_function_name(function))
        } else {
            self.generate_function_name(function)
        }
    }

    fn generate_get_function(&self, get_func: &GetFunction) -> Code {
        let target = &*get_func.target.borrow();
        let ptr_expr = self.generate_function_pointer_expression(target);

        Code::from_string(format!("stack.push_function_pointer({});", ptr_expr))
    }

    fn generate_match(&self, match_: &Match) -> Code {
        let enum_rc = match_.target.take().unwrap();
        match_.target.set(Some(enum_rc.clone()));

        let enum_ = &*enum_rc.borrow();
        let enum_name = self.generate_enum_name(enum_);

        let match_var = format!("match_var_{}", hash_position(&match_.position));

        let mut code = Code::new();

        code.add_line(format!(
            "let {} = stack.pop_user_type().borrow_mut().get_{}().clone();",
            match_var, enum_name
        ));

        code.add_line(format!("match {} {{", match_var));

        for case_block in &match_.case_blocks {
            code.add_code(self.generate_case_block(case_block, enum_));
        }

        for default_block in &match_.default_blocks {
            code.add_code(self.generate_default_block(default_block));
        }

        if match_.default_blocks.is_empty() && match_.case_blocks.len() != enum_.variants().len() {
            code.add_line("_ => {}");
        }

        code.add_line("}");

        code
    }

    fn generate_case_block(&self, block: &CaseBlock, enum_: &Enum) -> Code {
        let enum_name = self.generate_enum_name(enum_);

        // Number of data items associated with variant handled here
        let data_items = enum_.variants().get(&block.variant_name).unwrap().len();

        // We add the hash of location to prevent collisions with nested case blocks.
        let var_prefix = format!("case_var_{}", hash_position(&block.position));

        let mut line = format!("{}::variant_{}(", enum_name, block.variant_name);

        line += (0..data_items)
            .map(|i| format!("{var_prefix}_{}", i))
            .collect::<Vec<String>>()
            .join(", ")
            .as_str();

        line += ") => {";

        let mut code = Code::new();

        code.add_line(line);

        if block.variables.is_empty() {
            for i in 0..data_items {
                code.add_line(format!("stack.push({var_prefix}_{i});"));
            }
        } else {
            for (i, var) in zip(0.., &block.variables) {
                let var_name = &var.name;
                code.add_line(format!(
                    "let mut var_{var_name}: Variable<UserTypeEnum> = {var_prefix}_{i};"
                ));
            }
        }

        code.add_code(self.generate_function_body(&block.body));
        code.add_line("},");

        code
    }

    fn generate_default_block(&self, block: &DefaultBlock) -> Code {
        let mut code = Code::new();
        code.add_line("_ => {");
        code.add_code(self.generate_function_body(&block.body));
        code.add_line("}");

        code
    }

    fn generate_get_field(&self, get_field: &GetField) -> Code {
        let struct_rc = get_field.target.take().unwrap();
        get_field.target.set(Some(struct_rc.clone()));

        let struct_ = &*struct_rc.borrow();

        let struct_name = self.generate_struct_name(struct_);

        let mut code = Code::new();

        code.add_line("{");
        code.add_line("let popped = stack.pop_user_type();");
        code.add_line("let mut borrowed = (*popped).borrow_mut();");
        code.add_line(format!(
            "stack.push(borrowed.get_{}().{}.clone());",
            struct_name, get_field.field_name
        ));
        code.add_line("}");

        code
    }

    fn generate_set_field(&self, set_field: &SetField) -> Code {
        let struct_rc = set_field.target.take().unwrap();
        set_field.target.set(Some(struct_rc.clone()));

        let struct_ = &*struct_rc.borrow();

        let struct_name = self.generate_struct_name(struct_);

        let mut code = Code::new();

        code.add_code(self.generate_function_body(&set_field.body));

        code.add_line("{");

        code.add_line("let value = stack.pop();");
        code.add_line("let popped = stack.pop_user_type();");
        code.add_line("let mut borrowed = (*popped).borrow_mut();");
        code.add_line(format!(
            "borrowed.get_{}().{} = value;",
            struct_name, set_field.field_name
        ));
        code.add_line("}");

        code
    }

    fn generate_enum_definition(&self, enum_: &Enum) -> Code {
        let name = self.generate_enum_name(enum_);

        let mut code = Code::new();

        code.add_line(format!(
            "// Generated for: {} {}",
            enum_.position().path.display(),
            enum_.name()
        ));
        code.add_line("#[derive(Clone)]");

        code.add_line(format!("enum {} {{", name));

        for (variant_name, variant_data) in enum_.variants() {
            let mut line = format!("variant_{}(", variant_name);
            let data = vec!["Variable<UserTypeEnum>"; variant_data.len()].join(", ");
            line.push_str(&data);
            line.push_str("),");

            code.add_line(line);
        }

        code.add_line("}");
        code.add_line("");

        code
    }

    fn generate_enum_constructors(&self, enum_: &Enum) -> Code {
        let enum_name = self.generate_enum_name(enum_);

        let mut code = Code::new();

        for (variant_name, associated_data) in enum_.variants() {
            let enum_ctor_func_name =
                self.generate_enum_constructor_name(enum_, variant_name.clone());
            code.add_line(format!(
                "fn {}(stack: &mut Stack<UserTypeEnum>) {{",
                enum_ctor_func_name
            ));
            for (i, _) in associated_data.iter().enumerate().rev() {
                code.add_line(format!("let arg{} = stack.pop();", i));
            }

            let mut line = format!("let enum_ = {}::variant_{}(", enum_name, variant_name);

            line += (0..associated_data.len())
                .map(|i| format!("arg{}", i))
                .collect::<Vec<String>>()
                .join(", ")
                .as_str();
            line += ");";

            code.add_line(line);
            code.add_line(format!(
                "stack.push_user_type(UserTypeEnum::{}(enum_));",
                enum_name
            ));
            code.add_line("}");
            code.add_line("");
        }

        code
    }

    fn generate_enum_impl(&self, enum_: &Enum) -> Code {
        let enum_name = self.generate_enum_name(enum_);

        let mut code = Code::new();

        code.add_line(format!("impl {} {{", enum_name));
        code.add_line("fn new() -> Self {");
        code.add_line(format!("Self::variant_{}(", enum_.zero_variant_name()));

        for variant_data_item in enum_.zero_variant_data() {
            let zero_value = self.generate_type_zero_expression(variant_data_item);
            code.add_line(format!("{},", zero_value));
        }

        code.add_line(")");
        code.add_line("}");
        code.add_line("}");
        code.add_line("");

        code
    }

    #[allow(non_snake_case)]
    fn generate_enum_UserType_impl(&self, enum_: &Enum) -> Code {
        let mut code = Code::new();

        let enum_name = self.generate_enum_name(enum_);

        code.add_line(format!("impl UserType for {enum_name} {{"));

        code.add_line("fn type_id(&self) -> String {");
        code.add_line(format!("String::from(\"{}\")", enum_name));
        code.add_line("}");

        code.add_line("");

        code.add_line("fn clone_recursive(&self) -> Self {");
        code.add_line("match self {");

        for (variant_name, associated_data) in enum_.variants() {
            let mut line = format!("Self::variant_{variant_name}(");
            line += (0..associated_data.len())
                .map(|i| format!("arg{}", i))
                .collect::<Vec<String>>()
                .join(", ")
                .as_str();
            line += ") => {";

            code.add_line(line);

            code.add_line(format!("Self::variant_{variant_name}("));
            for i in 0..associated_data.len() {
                code.add_line(format!("arg{i}.clone_recursive(),"));
            }

            code.add_line(")");
            code.add_line("},");
        }

        code.add_line("}");
        code.add_line("}");
        code.add_line("}");
        code.add_line("");

        code
    }

    #[allow(non_snake_case)]
    fn generate_enum_Hash_impl(&self, enum_: &Enum) -> Code {
        let name = self.generate_enum_name(enum_);

        let mut code = Code::new();

        code.add_line(format!("impl Hash for {} {{", name));

        code.add_line("fn hash<H: std::hash::Hasher>(&self, state: &mut H) {");

        code.add_line("todo!();"); // TODO #125 Implement hash for structs and enums

        code.add_line("}");

        code.add_line("}");
        code.add_line("");

        code
    }

    #[allow(non_snake_case)]
    fn generate_enum_PartialEq_impl(&self, enum_: &Enum) -> Code {
        let mut code = Code::new();

        let name = self.generate_enum_name(enum_);

        code.add_line(format!("impl PartialEq for {} {{", name));

        code.add_line("fn eq(&self, other: &Self) -> bool {");

        code.add_line("todo!();"); // TODO Implement interfaces

        code.add_line("}");

        code.add_line("}");
        code.add_line("");

        code
    }

    fn generate_struct_definition(&self, struct_: &Struct) -> Code {
        let mut code = Code::new();

        let name = self.generate_struct_name(struct_);

        code.add_line(format!(
            "// Generated for {} {}",
            struct_.position().path.display(),
            struct_.name()
        ));

        code.add_line("#[derive(Clone)]");

        code.add_line(format!("struct {} {{", name));

        for field_name in struct_.fields().keys() {
            code.add_line(format!("{}: Variable<UserTypeEnum>,", field_name));
        }

        code.add_line("}");
        code.add_line("");

        code
    }

    fn generate_struct_impl(&self, struct_: &Struct) -> Code {
        let mut code = Code::new();

        let name = self.generate_struct_name(struct_);

        code.add_line(format!(
            "// Generated for: {} {}",
            struct_.position().path.display(),
            struct_.name()
        ));

        code.add_line(format!("impl {} {{", name));

        code.add_line("fn new() -> Self {");

        code.add_line("Self {");

        for (field_name, type_) in struct_.fields() {
            let zero_expression = self.generate_type_zero_expression(type_);
            code.add_line(format!("{}: {},", field_name, zero_expression));
        }

        code.add_line("}");

        code.add_line("}");

        code.add_line("}");
        code.add_line("");

        code
    }

    #[allow(non_snake_case)]
    fn generate_struct_UserType_impl(&self, struct_: &Struct) -> Code {
        let mut code = Code::new();

        let name = self.generate_struct_name(struct_);

        code.add_line(format!("impl UserType for {} {{", name));

        code.add_line("fn type_id(&self) -> String {");
        code.add_line(format!("String::from(\"{}\")", name));
        code.add_line("}");

        code.add_line("");

        code.add_line("fn clone_recursive(&self) -> Self {");

        code.add_line("Self {");

        for field_name in struct_.fields().keys() {
            code.add_line(format!(
                "{}: self.{}.clone_recursive(),",
                field_name, field_name
            ));
        }

        code.add_line("}");
        code.add_line("}");

        code.add_line("}");

        code.add_line("");
        code
    }

    #[allow(non_snake_case)]
    fn generate_struct_Hash_impl(&self, struct_: &Struct) -> Code {
        let name = self.generate_struct_name(struct_);

        let mut code = Code::new();

        code.add_line(format!("impl Hash for {} {{", name));

        code.add_line("fn hash<H: std::hash::Hasher>(&self, state: &mut H) {");

        code.add_line("todo!();"); // TODO #125 Support hash for structs and enums

        code.add_line("}");

        code.add_line("}");
        code.add_line("");

        code
    }

    #[allow(non_snake_case)]
    fn generate_struct_PartialEq_impl(&self, struct_: &Struct) -> Code {
        let mut code = Code::new();

        let name = self.generate_struct_name(struct_);

        code.add_line(format!("impl PartialEq for {} {{", name));

        code.add_line("fn eq(&self, other: &Self) -> bool {");

        code.add_line("todo!();"); // TODO Implement interfaces

        code.add_line("}");

        code.add_line("}");
        code.add_line("");

        code
    }

    fn generate_enum_constructor_name(&self, enum_: &Enum, variant_name: String) -> String {
        if enum_.is_builtin() {
            return format!("{}_{}", enum_.name(), variant_name).to_lowercase();
        }

        let function_name = format!("{}:{}", enum_.name(), variant_name);
        let hash = Self::hash_name(enum_.position().path, function_name);
        format!("enum_ctor_{}", hash)
    }

    fn generate_call_enum_constructor(&self, call: &CallEnumConstructor) -> Code {
        let enum_ctor = &*call.enum_constructor.borrow();
        let variant_name = enum_ctor.variant_name();
        let enum_ = &*enum_ctor.enum_.borrow();
        let enum_ctor_name = self.generate_enum_constructor_name(enum_, variant_name);

        if enum_.is_builtin() {
            Code::from_string(format!("stack.{}();", enum_ctor_name))
        } else {
            Code::from_string(format!("{}(stack);", enum_ctor_name))
        }
    }

    fn generate_call(&self) -> Code {
        Code::from_string("stack.pop_function_pointer_and_call();")
    }

    fn generate_call_interface_function(&self, call: &CallInterfaceFunction) -> Code {
        let mut code = Code::new();

        let interface = &call.function.interface.borrow();

        let interface_hash = if interface.is_builtin() {
            format!("builtins:{}", interface.name())
        } else {
            format!("user_type_{}", interface.hash())
        };

        let function_name = &call.function.function_name;

        code.add_line(format!(
            "stack.call_interface_function(\"{}\", \"{}\");",
            interface_hash, function_name,
        ));

        code
    }
}

use chrono::Local;
use sha2::{Digest, Sha256};

use crate::{
    common::{position::Position, traits::HasPosition},
    cross_referencer::{
        cross_referencer,
        types::{
            function_body::{
                Assignment, Boolean, Branch, CallArgument, CallEnum, CallFunction,
                CallLocalVariable, CallStruct, Char, FunctionBody, FunctionBodyItem, FunctionType,
                GetField, GetFunction, Integer, Match, ParsedString, Return, SetField, Use, While,
            },
            identifiable::{Enum, Function, Identifiable, ReturnTypes, Struct, Type},
        },
    },
    transpiler::code::Code,
};
use lazy_static::lazy_static;
use std::{cell::RefCell, collections::HashMap, env, fs, path::PathBuf, rc::Rc};

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
        ];

        HashMap::from(array)
    };
}

pub struct Transpiler {
    transpiler_root_path: PathBuf,
    pub identifiables: HashMap<(PathBuf, String), Identifiable>,
    pub entrypoint_path: PathBuf,
    pub structs: HashMap<(PathBuf, String), Rc<RefCell<Struct>>>,
    pub enums: HashMap<(PathBuf, String), Rc<RefCell<Enum>>>,
    pub functions: HashMap<(PathBuf, String), Rc<RefCell<Function>>>,
    pub position_stacks: HashMap<Position, Vec<Type>>,
}

impl Transpiler {
    pub fn new(
        transpiler_root_path: PathBuf,
        cross_referenced: cross_referencer::Output,
        position_stacks: HashMap<Position, Vec<Type>>,
    ) -> Self {
        let mut functions = HashMap::new();
        let mut structs = HashMap::new();
        let mut enums = HashMap::new();

        for (key, identifiable) in &cross_referenced.identifiables {
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
            identifiables: cross_referenced.identifiables,
            entrypoint_path: cross_referenced.entrypoint_path,
            structs,
            enums,
            functions,
            position_stacks,
        }
    }

    pub fn run(&self) {
        // TODO #225 Support runtime type checking

        let code = self.generate_file();

        fs::create_dir_all(&self.transpiler_root_path.join("src")).unwrap();
        let main_path = self.transpiler_root_path.join("src/main.rs");

        // TODO #215 use CLI args here instead of env var
        if env::var("AAA_DEBUG").is_ok() {
            println!("writing to {:?}", main_path);
        }

        fs::write(main_path, code.get()).unwrap();
    }

    fn generate_file(&self) -> Code {
        let mut code = Code::new();

        code.add_code(self.generate_header_comment());
        code.add_code(self.generate_warning_silencing_macros());
        code.add_code(self.generate_imports());

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
        code.add_line("use aaa_stdlib::stack::Stack;");
        code.add_line("use aaa_stdlib::set::{Set, SetValue};");
        code.add_line("use aaa_stdlib::var::{UserType, Variable};");
        code.add_line("use aaa_stdlib::vector::Vector;");
        code.add_line("use regex::Regex;");
        code.add_line("use std::cell::RefCell;");
        code.add_line("use std::collections::HashMap;");
        code.add_line("use std::fmt::{Debug, Display, Formatter, Result};");
        code.add_line("use std::hash::Hash;");
        code.add_line("use std::process;");
        code.add_line("use std::rc::Rc;");
        code.add_line("");

        code
    }

    #[allow(non_snake_case)]
    fn generate_UserTypeEnum(&self) -> Code {
        let mut code = Code::new();

        code.add_code(self.generate_UserTypeEnum_definition());
        code.add_code(self.generate_UserTypeEnum_impl());
        code.add_code(self.generate_UserTypeEnum_UserType_impl());
        code.add_code(self.generate_UserTypeEnum_Display_impl());
        code.add_code(self.generate_UserTypeEnum_Debug_impl());

        code
    }

    fn generate_enum(&self, enum_: &Enum) -> Code {
        let mut code = Code::new();

        code.add_code(self.generate_enum_definition(enum_));
        code.add_code(self.generate_enum_constructors(enum_));
        code.add_code(self.generate_enum_impl(enum_));
        code.add_code(self.generate_enum_UserType_impl(enum_));
        code.add_code(self.generate_enum_Display_impl(enum_));
        code.add_code(self.generate_enum_Debug_impl(enum_));
        code.add_code(self.generate_enum_Hash_impl(enum_));
        code.add_code(self.generate_enum_PartialEq_impl(enum_));

        code
    }

    fn generate_struct(&self, struct_: &Struct) -> Code {
        let mut code = Code::new();

        code.add_code(self.generate_struct_definition(struct_));
        code.add_code(self.generate_struct_impl(struct_));
        code.add_code(self.generate_struct_UserType_impl(struct_));
        code.add_code(self.generate_struct_Display_impl(struct_));
        code.add_code(self.generate_struct_Debug_impl(struct_));
        code.add_code(self.generate_struct_Hash_impl(struct_));
        code.add_code(self.generate_struct_PartialEq_impl(struct_));

        code
    }

    #[allow(non_snake_case)]
    fn generate_UserTypeEnum_definition(&self) -> Code {
        let mut code = Code::new();
        code.add_line("#[derive(Clone, Hash, PartialEq)]");
        code.add_line("enum UserTypeEnum {");

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
        return code;
    }

    #[allow(non_snake_case)]
    fn generate_UserTypeEnum_UserType_impl(&self) -> Code {
        let mut code = Code::new();
        code.add_line("impl UserType for UserTypeEnum {");

        code.add_line("fn kind(&self) -> String {");
        code.add_line("todo!();"); // TODO #219 Implement Enum
        code.add_line("}");

        code.add_line("");

        code.add_line("fn clone_recursive(&self) -> Self {");
        code.add_line("todo!();"); // TODO #219 Implement Enum
        code.add_line("}");

        code.add_line("}");
        code.add_line("");

        code
    }

    #[allow(non_snake_case)]
    fn generate_UserTypeEnum_Display_impl(&self) -> Code {
        let mut code = Code::new();

        code.add_line("impl Display for UserTypeEnum {");

        code.add_line("fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {");

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

        if names.is_empty() {
            code.add_line("unreachable!();");
        } else {
            code.add_line("match self {");

            for name in names {
                code.add_line(format!("Self::{}(v) => write!(f, \"{{}}\", v),", name));
            }

            code.add_line("}");
        }

        code.add_line("}");

        code.add_line("}");
        code.add_line("");

        code
    }

    #[allow(non_snake_case)]
    fn generate_UserTypeEnum_Debug_impl(&self) -> Code {
        let mut code = Code::new();
        code.add_line("impl Debug for UserTypeEnum {");

        code.add_line("fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {");
        code.add_line("todo!();"); // TODO #219 Implement Enum
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

        function_name.replace(":", "_")
    }

    fn hash_name(path: PathBuf, name: String) -> String {
        let mut hasher = Sha256::new();
        hasher.update(path.to_string_lossy().as_bytes());
        hasher.update(name.as_bytes());

        let hash = hasher.finalize();
        let hash = format!("{:x}", hash);

        hash[..16].to_owned()
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
        let key = (self.entrypoint_path.clone(), "main".to_owned());
        let main_function = self.identifiables.get(&key).unwrap();

        let Identifiable::Function(main_function) = main_function else {
            unreachable!();
        };

        let main_function = &*main_function.borrow();

        let main_func_name = self.generate_function_name(main_function);

        let mut code = Code::new();
        code.add_line("fn main() {");

        if main_function.arguments().is_empty() {
            code.add_line("let mut stack: Stack<UserTypeEnum> = Stack::new();");
        } else {
            code.add_line("let mut stack:Stack<UserTypeEnum> = Stack::from_argv();");
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
            Branch(branch) => self.generate_branch(branch),
            Boolean(bool) => self.generate_boolean(bool),
            Call(_) => unreachable!(), // TODO #220 Support Call
            CallArgument(call) => self.generate_call_argument(call),
            CallFunction(call) => self.generate_call_function(call),
            CallEnum(call) => self.generate_call_enum(call),
            CallEnumConstructor(_) => unreachable!(), // TODO #219 Support CallEnumConstructor
            CallLocalVariable(call) => self.generate_call_local_variabiable(call),
            CallStruct(call) => self.generate_call_struct(call),
            Char(char) => self.generate_char(char),
            Foreach(_) => unreachable!(), // TODO #214 support interfaces
            FunctionType(function_type) => self.generate_function_type(function_type),
            GetFunction(get_function) => self.generate_get_function(get_function),
            Integer(integer) => self.generate_integer(integer),
            Match(match_) => self.generate_match(match_),
            Return(return_) => self.generate_return(return_),
            GetField(get_field) => self.generate_get_field(get_field),
            SetField(set_field) => self.generate_set_field(set_field),
            Use(use_) => self.generate_use(use_),
            While(while_) => self.generate_while(while_),
            String(string) => self.generate_string(string),
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
            _ => unreachable!(),
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

    fn generate_match(&self, _: &Match) -> Code {
        todo!(); // TODO #219 Implement Enum
    }

    fn get_stack_top_struct(&self, position: &Position) -> Rc<RefCell<Struct>> {
        // TODO #217 remove position_stacks and this function
        // TODO #217 make GetField and SetField have a target Struct field

        let Some(stack) = self.position_stacks.get(position) else {
            unreachable!();
        };

        let Some(top_type) = stack.last() else {
            unreachable!();
        };

        let Type::Struct(struct_type) = top_type else {
            unreachable!();
        };

        struct_type.struct_.clone()
    }

    fn generate_get_field(&self, get_field: &GetField) -> Code {
        let struct_ = self.get_stack_top_struct(&get_field.position);
        let struct_ = &*struct_.borrow();

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
        let struct_ = self.get_stack_top_struct(&set_field.position);
        let struct_ = &*struct_.borrow();

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
            "//Generated for: {} {}",
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

    fn generate_enum_constructors(&self, _enum_: &Enum) -> Code {
        let mut code = Code::new();
        code.add_line("// TODO implement generate_enum_constructors()"); // TODO #219 Support Enum
        code.add_line("");
        code
    }

    fn generate_enum_impl(&self, _enum_: &Enum) -> Code {
        let mut code = Code::new();
        code.add_line("// TODO implement generate_enum_impl()"); // TODO #219 Support Enum
        code.add_line("");
        code
    }

    #[allow(non_snake_case)]
    fn generate_enum_UserType_impl(&self, _enum_: &Enum) -> Code {
        let mut code = Code::new();
        code.add_line("// TODO implement generate_enum_UserType_impl()"); // TODO #219 Support Enum
        code.add_line("");
        code
    }

    #[allow(non_snake_case)]
    fn generate_enum_Display_impl(&self, _enum_: &Enum) -> Code {
        let mut code = Code::new();
        code.add_line("// TODO implement generate_enum_Display_impl()"); // TODO #219 Support Enum
        code.add_line("");
        code
    }

    #[allow(non_snake_case)]
    fn generate_enum_Debug_impl(&self, _enum_: &Enum) -> Code {
        let mut code = Code::new();
        code.add_line("// TODO implement generate_enum_Debug_impl()"); // TODO #219 Support Enum
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

        return code;
    }

    #[allow(non_snake_case)]
    fn generate_enum_PartialEq_impl(&self, enum_: &Enum) -> Code {
        let mut code = Code::new();

        let name = self.generate_enum_name(enum_);

        code.add_line(format!("impl PartialEq for {} {{", name));

        code.add_line("fn eq(&self, other: &Self) -> bool {");

        code.add_line("todo!();"); // TODO #219 implement generate_enum_PartialEq_impl()

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

        code.add_line("fn kind(&self) -> String {");
        code.add_line(format!("String::from(\"{}\")", struct_.name()));
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
    fn generate_struct_Display_impl(&self, struct_: &Struct) -> Code {
        let name = self.generate_struct_name(struct_);

        let mut code = Code::new();

        code.add_line(format!("impl Display for {} {{", name));

        code.add_line("fn fmt(&self, f: &mut Formatter<'_>) -> Result {");

        code.add_line(format!("write!(f, \"{}{{{{\")?;", name));

        for (offset, field_name) in struct_.fields().keys().enumerate() {
            if offset != 0 {
                code.add_line("write!(f, \", \")?;");
            }

            code.add_line(format!(
                "write!(f, \"{}: {{}}\", self.{})?;",
                field_name, field_name
            ));
        }

        code.add_line("write!(f, \"}}\")");

        code.add_line("}");

        code.add_line("}");
        code.add_line("");

        return code;
    }

    #[allow(non_snake_case)]
    fn generate_struct_Debug_impl(&self, struct_: &Struct) -> Code {
        let name = self.generate_struct_name(struct_);

        let mut code = Code::new();

        code.add_line(format!("impl Debug for {} {{", name));

        code.add_line("fn fmt(&self, f: &mut Formatter<'_>) -> Result {");

        code.add_line(format!("write!(f, \"{}{{{{\")?;", name));

        for (offset, field_name) in struct_.fields().keys().enumerate() {
            if offset != 0 {
                code.add_line("write!(f, \", \")?;");
            }

            code.add_line(format!(
                "write!(f, \"{}: {{:?}}\", self.{})?;",
                field_name, field_name
            ));
        }

        code.add_line("write!(f, \"}}\")");

        code.add_line("}");

        code.add_line("}");
        code.add_line("");

        return code;
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

        return code;
    }

    #[allow(non_snake_case)]
    fn generate_struct_PartialEq_impl(&self, struct_: &Struct) -> Code {
        let mut code = Code::new();

        let name = self.generate_struct_name(struct_);

        code.add_line(format!("impl PartialEq for {} {{", name));

        code.add_line("fn eq(&self, other: &Self) -> bool {");

        code.add_line("todo!();"); // TODO #219 implement generate_enum_PartialEq_impl()

        code.add_line("}");

        code.add_line("}");
        code.add_line("");

        code
    }
}

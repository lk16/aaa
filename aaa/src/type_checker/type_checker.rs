#![allow(clippy::result_large_err)] // TODO #239 Handle linter error for large error result

use std::{
    cell::RefCell,
    collections::{HashMap, HashSet},
    fmt::Display,
    iter::zip,
    path::PathBuf,
    rc::Rc,
};

use crate::{
    common::{formatting::join_display, position::Position, traits::HasPosition},
    cross_referencer::{
        cross_referencer,
        types::{
            function_body::{
                Assignment, Branch, Call, CallArgument, CallEnum, CallEnumConstructor,
                CallFunction, CallLocalVariable, CallStruct, CaseBlock, Foreach, FunctionBody,
                FunctionBodyItem, FunctionType, GetField, GetFunction, Match, Return, SetField,
                Use, While,
            },
            identifiable::{
                Argument, EnumType, Function, FunctionPointerType, Identifiable, ReturnTypes,
                StructType, Type,
            },
        },
    },
    type_checker::errors::{
        assigned_variable_not_found, assignment_stack_size_error, call_non_function,
        colliding_case_blocks, colliding_default_blocks, does_not_return,
        get_field_from_non_struct, invalid_main_signature, main_function_not_found,
        match_stack_underflow, match_unexpected_enum, member_function_unexpected_target,
        name_collision, unexpected_case_variable_count, unhandled_enum_variants,
    },
};

use super::{
    call_checker::CallChecker,
    errors::{
        assignment_type_error, branch_error, call_stack_underflow, condition_error,
        function_type_error, get_field_not_found, get_field_stack_underflow,
        inconsistent_match_children, main_non_function, match_non_enum,
        member_function_invalid_target, member_function_without_arguments, parameter_count_error,
        return_stack_error, set_field_not_found, set_field_on_non_struct,
        set_field_stack_underflow, set_field_type_error, unreachable_code, unreachable_default,
        use_stack_underflow, while_error, TypeError, TypeResult,
    },
};

pub struct TypeChecker {
    pub identifiables: HashMap<(PathBuf, String), Identifiable>,
    pub builtins_path: PathBuf,
    pub entrypoint_path: PathBuf,
    pub verbose: bool,
}

pub struct Output {
    pub main_function: Rc<RefCell<Function>>,
    pub identifiables: HashMap<(PathBuf, String), Identifiable>,
}

pub fn type_check(
    input: cross_referencer::Output,
    verbose: bool,
) -> Result<Output, Vec<TypeError>> {
    TypeChecker::new(input, verbose).run()
}

impl TypeChecker {
    fn new(input: cross_referencer::Output, verbose: bool) -> Self {
        Self {
            identifiables: input.identifiables,
            builtins_path: input.builtins_path,
            entrypoint_path: input.entrypoint_path,
            verbose,
        }
    }

    fn functions(&self) -> Vec<Rc<RefCell<Function>>> {
        let mut functions = vec![];

        for identifiable in self.identifiables.values() {
            if let Identifiable::Function(function_rc) = identifiable {
                functions.push(function_rc.clone())
            }
        }

        // Sort functions by position, to have a reproducible sequence of errors.
        functions.sort_by_key(|f| (**f).borrow().position());

        functions
    }

    fn run(self) -> Result<Output, Vec<TypeError>> {
        let mut errors = vec![];

        for function_rc in self.functions() {
            let function = &*(*function_rc).borrow();
            let checker = FunctionTypeChecker::new(function, &self);

            if let Err(error) = checker.run() {
                errors.push(error);
            }
        }

        let mut main_function: Option<Rc<RefCell<Function>>> = None;

        match self.check_main_function() {
            Err(error) => errors.push(error),
            Ok(function) => main_function = Some(function),
        }

        if !errors.is_empty() {
            return Err(errors);
        }

        let output = Output {
            main_function: main_function.unwrap(),
            identifiables: self.identifiables,
        };

        Ok(output)
    }

    fn check_main_function(&self) -> Result<Rc<RefCell<Function>>, TypeError> {
        let key = (self.entrypoint_path.clone(), "main".to_owned());

        let Some(identifiable) = self.identifiables.get(&key) else {
            return main_function_not_found(self.entrypoint_path.clone());
        };

        let Identifiable::Function(function_rc) = identifiable else {
            return main_non_function(identifiable.position(), identifiable.clone());
        };

        let function = &*function_rc.borrow();

        let arguments = function.arguments();

        match arguments.len() {
            0 => (),
            1 => {
                let argument_type = &arguments.first().unwrap().type_;
                if !self.is_valid_main_argument_type(argument_type) {
                    return invalid_main_signature(function.position());
                }
            }
            _ => return invalid_main_signature(function.position()),
        }

        match function.return_types() {
            ReturnTypes::Never => (),
            ReturnTypes::Sometimes(return_types) => match return_types.len() {
                0 => (),
                1 => {
                    let return_type = return_types.first().unwrap();
                    if !self.is_valid_main_return_type(return_type) {
                        return invalid_main_signature(function.position());
                    }
                }
                _ => return invalid_main_signature(function.position()),
            },
        }

        Ok(function_rc.clone())
    }

    fn is_valid_main_argument_type(&self, type_: &Type) -> bool {
        let Type::Struct(struct_type) = type_ else {
            return false;
        };

        let parameters = struct_type.parameters.clone();

        let struct_ = &*struct_type.struct_.borrow();

        if struct_.name().as_str() != "vec" {
            return false;
        }

        if parameters.len() != 1 {
            return false;
        }

        let parameter = parameters.first().unwrap();

        let Type::Struct(parameter_struct_type) = parameter else {
            return false;
        };

        let parameter_struct = &*parameter_struct_type.struct_.borrow();

        if parameter_struct.name().as_str() != "str" {
            return false;
        }

        true
    }

    fn is_valid_main_return_type(&self, type_: &Type) -> bool {
        let Type::Struct(struct_type) = type_ else {
            return false;
        };

        let struct_ = &*struct_type.struct_.borrow();

        if struct_.name().as_str() != "int" {
            return false;
        }

        true
    }
}

#[derive(Clone)]
pub struct LocalVariable {
    pub name: String,
    pub type_: Type,
    pub position: Position,
}

impl HasPosition for LocalVariable {
    fn position(&self) -> Position {
        self.position.clone()
    }
}

impl Display for LocalVariable {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "local variable {}", self.name)
    }
}

impl From<Argument> for LocalVariable {
    fn from(argument: Argument) -> Self {
        Self {
            name: argument.name.clone(),
            type_: argument.type_.clone(),
            position: argument.position(),
        }
    }
}

pub struct FunctionTypeChecker<'a> {
    function: &'a Function,
    type_checker: &'a TypeChecker,
    local_variables: HashMap<String, LocalVariable>,
}

impl<'a> FunctionTypeChecker<'a> {
    fn new(function: &'a Function, type_checker: &'a TypeChecker) -> Self {
        let local_variables = function
            .arguments()
            .iter()
            .map(|arg| (arg.name.clone(), arg.clone().into()))
            .collect();

        Self {
            function,
            type_checker,
            local_variables,
        }
    }

    fn run(mut self) -> Result<(), TypeError> {
        if self.function.is_builtin {
            return Ok(());
        }

        self.print_signature();

        // TODO #218 Check signature if this is a test

        self.check_member_function_signature()?;

        let computed = self.check_function_body(vec![], self.function.body());

        let computed = match computed {
            Ok(types) => ReturnTypes::Sometimes(types),
            Err(TypeError::DoesNotReturn) => ReturnTypes::Never,
            Err(error) => return Err(error),
        };

        if self.type_checker.verbose {
            println!("computed return type: {}", computed);
        }

        if !self.confirm_return_types(&computed) {
            return function_type_error(
                self.function.position(),
                self.function.name(),
                computed,
                self.function.signature().return_types.clone(),
            );
        }

        Ok(())
    }

    fn confirm_return_types(&self, computed: &ReturnTypes) -> bool {
        use ReturnTypes::*;

        let expected = &self.function.signature().return_types;

        match (computed, expected) {
            (Sometimes(computed), Sometimes(expected)) => computed == expected,
            (Sometimes(_), Never) => false,
            (Never, _) => true,
        }
    }

    fn print_signature(&self) {
        if !self.type_checker.verbose {
            return;
        }

        println!("position: {}", self.function.position());
        println!("function: {}", self.function.name());

        for argument in &self.function.signature().arguments {
            println!("argument {}: {}", argument.name, argument.type_)
        }

        println!("returns: {}", &self.function.signature().return_types);
        println!();
    }

    fn print_position_stack(&mut self, position: Position, stack: &[Type]) {
        if !self.type_checker.verbose {
            return;
        }

        let stack_types = join_display(" ", stack);
        println!("{} {}", position, stack_types);
    }

    fn builtin_type(&self, name: &str) -> Type {
        let builtins_path = self.type_checker.builtins_path.clone();
        let key = (builtins_path, name.to_string());

        let Some(identifiable) = self.type_checker.identifiables.get(&key) else {
            panic!(
                "builtin_type() could not find identifiable with key ({:?},{})",
                &key.0, &key.1
            );
        };

        let Identifiable::Struct(struct_) = identifiable else {
            panic!("builtin_type() only handles structs");
        };

        Type::Struct(StructType {
            struct_: struct_.clone(),
            parameters: vec![],
        })
    }

    fn check_member_function_signature(&self) -> Result<(), TypeError> {
        let Some(type_name) = self.function.type_name() else {
            return Ok(());
        };

        let position = self.function.position();
        let name = self.function.name();

        let Some(first_argument) = self.function.arguments().first() else {
            return member_function_without_arguments(position, name);
        };

        let first_arg_type_name = match &first_argument.type_ {
            Type::Enum(enum_type) => enum_type.enum_.borrow().name(),
            Type::Struct(struct_type) => struct_type.struct_.borrow().name(),
            _ => {
                return member_function_invalid_target(position, name, first_argument.type_.clone())
            }
        };

        if type_name != first_arg_type_name {
            return member_function_unexpected_target(
                position,
                name,
                type_name,
                first_arg_type_name,
            );
        }

        Ok(())
    }

    fn check_function_body(&mut self, mut stack: Vec<Type>, body: &FunctionBody) -> TypeResult {
        for (i, item) in body.items.iter().enumerate() {
            self.print_position_stack(item.position(), &stack);

            let item_result = self.check_function_body_item(stack, item);

            if let Err(TypeError::DoesNotReturn) = item_result {
                if let Some(unreachable_item) = body.items.get(i + 1) {
                    return unreachable_code(unreachable_item.position());
                };
            }

            stack = item_result?;
        }

        Ok(stack)
    }

    fn check_function_body_item(
        &mut self,
        stack: Vec<Type>,
        item: &FunctionBodyItem,
    ) -> TypeResult {
        use FunctionBodyItem::*;

        match item {
            Integer(_) => self.check_integer(stack),
            String(_) => self.check_string(stack),
            Boolean(_) => self.check_boolean(stack),
            Char(_) => self.check_character(stack),
            Branch(branch) => self.check_branch(stack, branch),
            While(while_) => self.check_while(stack, while_),
            CallFunction(call) => self.check_call_function(stack, call),
            CallStruct(call) => self.check_call_struct(stack, call),
            FunctionType(func_type) => self.check_function_type(stack, func_type),
            CallEnum(call) => self.check_call_enum(stack, call),
            CallArgument(call) => self.check_call_argument(stack, call),
            Return(return_) => self.check_return(stack, return_),
            Use(use_) => self.check_use(stack, use_),
            CallLocalVariable(call) => self.check_call_local_variable(stack, call),
            GetField(get_field) => self.check_get_field(stack, get_field),
            SetField(set_field) => self.check_set_field(stack, set_field),
            Assignment(assignment) => self.check_assignment(stack, assignment),
            GetFunction(get_function) => self.check_get_function(stack, get_function),
            Foreach(foreach) => self.check_foreach(stack, foreach),
            Match(match_) => self.check_match(stack, match_),
            CallEnumConstructor(call) => self.check_call_enum_constructor(stack, call),
            Call(call) => self.check_call(stack, call),
        }
    }

    fn check_integer(&self, mut stack: Vec<Type>) -> TypeResult {
        stack.push(self.builtin_type("int"));
        Ok(stack)
    }

    fn check_string(&self, mut stack: Vec<Type>) -> TypeResult {
        stack.push(self.builtin_type("str"));
        Ok(stack)
    }

    fn check_boolean(&self, mut stack: Vec<Type>) -> TypeResult {
        stack.push(self.builtin_type("bool"));
        Ok(stack)
    }

    fn check_character(&self, mut stack: Vec<Type>) -> TypeResult {
        stack.push(self.builtin_type("char"));
        Ok(stack)
    }

    fn check_condition_body(&mut self, stack: Vec<Type>, body: &FunctionBody) -> TypeResult {
        let mut stack_after = self.check_function_body(stack.clone(), body)?;

        let mut expected_stack_after = stack.clone();
        expected_stack_after.push(self.builtin_type("bool"));

        if stack_after != expected_stack_after {
            let position = body.position.clone();
            return condition_error(position, stack.clone(), stack_after, expected_stack_after);
        }

        // Emulate boolean being removed from top when condition is checked
        stack_after.pop();

        Ok(stack_after)
    }

    fn check_branch(&mut self, stack: Vec<Type>, branch: &Branch) -> TypeResult {
        let condition_stack = self.check_condition_body(stack, &branch.condition)?;

        let if_stack_result = self.check_function_body(condition_stack.clone(), &branch.if_body);

        let else_stack_result = match &branch.else_body {
            None => Ok(condition_stack.clone()),
            Some(else_body) => self.check_function_body(condition_stack.clone(), else_body),
        };

        let if_stack = match if_stack_result {
            Err(TypeError::DoesNotReturn) => return else_stack_result,
            Err(_) => return if_stack_result,
            Ok(if_stack) => if_stack,
        };

        let else_stack = match else_stack_result {
            Err(TypeError::DoesNotReturn) => return Ok(if_stack),
            Err(_) => return else_stack_result,
            Ok(else_stack) => else_stack,
        };

        if if_stack != else_stack {
            return branch_error(
                branch.position.clone(),
                condition_stack,
                if_stack,
                else_stack,
            );
        }

        Ok(if_stack)
    }

    fn check_while(&mut self, stack: Vec<Type>, while_: &While) -> TypeResult {
        let condition_stack = self.check_condition_body(stack, &while_.condition)?;

        let body_stack = self.check_function_body(condition_stack.clone(), &while_.body)?;

        if body_stack != condition_stack {
            return while_error(while_.position.clone(), condition_stack, body_stack);
        }

        Ok(condition_stack)
    }

    fn check_call_function(&self, stack: Vec<Type>, call: &CallFunction) -> TypeResult {
        let function = &*(*call.function).borrow();
        let signature = function.signature();

        let checker = CallChecker {
            type_params: signature.type_parameters.clone(),
            argument_types: signature.argument_types(),
            return_types: signature.return_types.clone(),
            name: function.name(),
            position: call.position.clone(),
            stack,
        };

        checker.check()
    }

    fn check_call_struct(&self, mut stack: Vec<Type>, call: &CallStruct) -> TypeResult {
        let expected_param_count = (*call.struct_).borrow().expected_parameter_count();
        let found_param_count = call.type_parameters.len();

        if call.type_parameters.len() != expected_param_count {
            return parameter_count_error(
                call.position.clone(),
                found_param_count,
                expected_param_count,
            );
        }

        let type_ = Type::Struct(StructType {
            struct_: call.struct_.clone(),
            parameters: call.type_parameters.clone(),
        });

        stack.push(type_);

        Ok(stack)
    }

    fn check_call_enum(&self, mut stack: Vec<Type>, call: &CallEnum) -> TypeResult {
        let expected_param_count = (*call.enum_).borrow().expected_parameter_count();
        let found_param_count = call.type_parameters.len();

        if call.type_parameters.len() != expected_param_count {
            return parameter_count_error(
                call.position.clone(),
                found_param_count,
                expected_param_count,
            );
        }

        let type_ = Type::Enum(EnumType {
            enum_: call.enum_.clone(),
            parameters: call.type_parameters.clone(),
        });

        stack.push(type_);

        Ok(stack)
    }

    fn check_function_type(&self, mut stack: Vec<Type>, func_type: &FunctionType) -> TypeResult {
        let type_ = Type::FunctionPointer(FunctionPointerType {
            argument_types: func_type.argument_types.clone(),
            return_types: func_type.return_types.clone(),
        });

        stack.push(type_);

        Ok(stack)
    }

    fn check_call_argument(&self, mut stack: Vec<Type>, call_arg: &CallArgument) -> TypeResult {
        let argument = self
            .function
            .signature()
            .arguments
            .iter()
            .find(|arg| arg.name == call_arg.name)
            .unwrap();

        let argument_type = argument.type_.clone();

        stack.push(argument_type);

        Ok(stack)
    }

    fn check_return(&self, stack: Vec<Type>, return_: &Return) -> TypeResult {
        let return_types = ReturnTypes::Sometimes(stack.clone());

        if !self.confirm_return_types(&return_types) {
            let expected = self.function.signature().return_types.clone();
            return return_stack_error(return_.position.clone(), return_types, expected);
        }

        does_not_return()
    }

    fn check_variable_name_availability(&self, local_var: &LocalVariable) -> Result<(), TypeError> {
        let name = &local_var.name;
        let file = &local_var.position().path;
        let key = (file.clone(), name.clone());
        let builtins_key = (self.type_checker.builtins_path.clone(), name.clone());

        let boxed_local_var = Box::new(local_var.clone());

        if let Some(argument) = self.function.get_argument(name) {
            let colliding = Box::new(argument.clone());
            return name_collision(boxed_local_var, colliding);
        }

        if let Some(identifiable) = self.type_checker.identifiables.get(&key) {
            let colliding = Box::new(identifiable.clone());
            return name_collision(boxed_local_var, colliding);
        }

        if let Some(identifiable) = self.type_checker.identifiables.get(&builtins_key) {
            let colliding = Box::new(identifiable.clone());
            return name_collision(boxed_local_var, colliding);
        }

        if let Some(colliding_local_var) = self.local_variables.get(name) {
            let colliding = Box::new(colliding_local_var.clone());
            return name_collision(boxed_local_var, colliding);
        }

        Ok(())
    }

    fn check_use(&mut self, mut stack: Vec<Type>, use_: &Use) -> TypeResult {
        let used_var_count = use_.variables.len();

        if used_var_count > stack.len() {
            return use_stack_underflow(use_.position.clone(), stack, used_var_count);
        }

        let top = stack.split_off(stack.len() - used_var_count);

        for (variable, type_) in zip(&use_.variables, top) {
            let var_name = variable.name.clone();

            let local_var = LocalVariable {
                name: var_name.clone(),
                position: variable.position.clone(),
                type_,
            };

            self.check_variable_name_availability(&local_var)?;

            self.local_variables.insert(var_name, local_var);
        }

        let body_result = self.check_function_body(stack, &use_.body);

        for variable in use_.variables.iter() {
            self.local_variables.remove(&variable.name);
        }

        body_result
    }

    fn check_call_local_variable(
        &self,
        mut stack: Vec<Type>,
        call: &CallLocalVariable,
    ) -> TypeResult {
        // CrossReferencer makes sure that this name exists
        let type_ = self.local_variables.get(&call.name).unwrap().type_.clone();

        stack.push(type_.clone());

        Ok(stack)
    }

    fn check_get_field(&self, mut stack: Vec<Type>, get_field: &GetField) -> TypeResult {
        let Some(type_) = stack.pop() else {
            return get_field_stack_underflow(
                get_field.position.clone(),
                get_field.field_name.clone(),
            );
        };

        let Type::Struct(struct_type) = type_ else {
            return get_field_from_non_struct(
                get_field.position.clone(),
                get_field.field_name.clone(),
                type_,
            );
        };

        // Update target, such that we can use this in transpiler
        get_field.target.set(Some(struct_type.struct_.clone()));

        let struct_ = (*struct_type.struct_).borrow();

        let Some(field_type) = struct_.field(&get_field.field_name) else {
            return get_field_not_found(
                get_field.position.clone(),
                get_field.field_name.clone(),
                struct_.name(),
            );
        };

        let type_parameters = struct_.parameter_mapping(&struct_type.parameters);

        let field_type = CallChecker::apply_type_params(field_type, &type_parameters);

        stack.push(field_type);

        Ok(stack)
    }

    fn check_set_field(&mut self, mut stack: Vec<Type>, set_field: &SetField) -> TypeResult {
        let Some(type_) = stack.pop() else {
            return set_field_stack_underflow(
                set_field.position.clone(),
                set_field.field_name.clone(),
            );
        };

        let Type::Struct(struct_type) = type_ else {
            return set_field_on_non_struct(
                set_field.position.clone(),
                set_field.field_name.clone(),
                type_,
            );
        };

        // Update target, such that we can use this in transpiler
        set_field.target.set(Some(struct_type.struct_.clone()));

        let struct_ = (*struct_type.struct_).borrow();

        let Some(field_type) = struct_.field(&set_field.field_name) else {
            return set_field_not_found(
                set_field.position.clone(),
                set_field.field_name.clone(),
                struct_.name(),
            );
        };

        let body_stack = self.check_function_body(vec![], &set_field.body)?;

        let type_parameters = struct_.parameter_mapping(&struct_type.parameters);

        let expected_body_stack_top = CallChecker::apply_type_params(field_type, &type_parameters);

        let expected_body_stack = vec![expected_body_stack_top];

        if body_stack != expected_body_stack {
            return set_field_type_error(
                set_field.position.clone(),
                set_field.field_name.clone(),
                struct_.name(),
                expected_body_stack,
                body_stack,
            );
        }

        Ok(stack)
    }

    fn check_foreach(&self, _stack: Vec<Type>, _for_each: &Foreach) -> TypeResult {
        todo!() // TODO Implement interfaces
    }

    fn check_assignment(&mut self, stack: Vec<Type>, assignment: &Assignment) -> TypeResult {
        let body_stack = self.check_function_body(vec![], &assignment.body)?;

        if assignment.variables.len() != body_stack.len() {
            return assignment_stack_size_error(
                assignment.position.clone(),
                assignment.variables.len(),
                body_stack.len(),
            );
        }

        for (variable, assigned_type) in zip(&assignment.variables, &body_stack) {
            let Some(local_var) = self.local_variables.get(&variable.name) else {
                return assigned_variable_not_found(
                    assignment.position.clone(),
                    variable.name.clone(),
                );
            };

            if &local_var.type_ != assigned_type {
                return assignment_type_error(
                    assignment.position.clone(),
                    variable.name.clone(),
                    local_var.type_.clone(),
                    assigned_type.clone(),
                );
            }
        }

        Ok(stack)
    }

    fn check_get_function(&self, mut stack: Vec<Type>, get_function: &GetFunction) -> TypeResult {
        let function = &*get_function.target.borrow();
        let signature = function.signature();

        let function_type = Type::FunctionPointer(FunctionPointerType {
            argument_types: signature.argument_types(),
            return_types: signature.return_types.clone(),
        });

        stack.push(function_type);

        Ok(stack)
    }

    fn check_match(&mut self, mut stack: Vec<Type>, match_: &Match) -> TypeResult {
        let Some(type_) = stack.pop() else {
            return match_stack_underflow(match_.position.clone());
        };

        let Type::Enum(enum_type) = type_ else {
            return match_non_enum(match_.position.clone(), type_);
        };

        // Update target, such that we can use this in transpiler
        match_.target.set(Some(enum_type.enum_.clone()));

        Self::check_match_is_expected_enum(&enum_type, match_)?;
        Self::check_match_is_full_enumeration(&enum_type, match_)?;

        stack = self.check_match_child_stacks(&stack, &enum_type, match_)?;

        Ok(stack)
    }

    fn check_match_is_expected_enum(enum_type: &EnumType, match_: &Match) -> Result<(), TypeError> {
        let enum_ = (*enum_type.enum_).borrow();

        for case_block in &match_.case_blocks {
            if case_block.enum_name.clone() != enum_.name() {
                return match_unexpected_enum(
                    case_block.position.clone(),
                    enum_.name(),
                    case_block.enum_name.clone(),
                );
            }
        }

        Ok(())
    }

    fn check_match_is_full_enumeration(
        enum_type: &EnumType,
        match_: &Match,
    ) -> Result<(), TypeError> {
        let enum_ = (*enum_type.enum_).borrow();

        let mut found_cases: HashMap<String, Position> = HashMap::new();

        for case_block in &match_.case_blocks {
            if let Some(colliding_position) =
                found_cases.insert(case_block.variant_name.clone(), case_block.position.clone())
            {
                return colliding_case_blocks(
                    case_block.enum_name.clone(),
                    case_block.variant_name.clone(),
                    [colliding_position, case_block.position.clone()],
                );
            };
        }

        if match_.default_blocks.len() > 1 {
            return colliding_default_blocks([
                match_.default_blocks.first().unwrap().position.clone(),
                match_.default_blocks.get(1).unwrap().position.clone(),
            ]);
        }

        let missing_cases: HashSet<_> = enum_
            .resolved()
            .variants
            .keys()
            .filter(|variant_name| !found_cases.contains_key(*variant_name))
            .cloned()
            .collect();

        if !missing_cases.is_empty() && match_.default_blocks.is_empty() {
            return unhandled_enum_variants(match_.position.clone(), enum_.name(), missing_cases);
        }

        if missing_cases.is_empty() && !match_.default_blocks.is_empty() {
            let default_position = match_.default_blocks.first().unwrap().position.clone();
            return unreachable_default(default_position);
        }

        Ok(())
    }

    fn check_match_child_stacks(
        &mut self,
        stack: &[Type],
        enum_type: &EnumType,
        match_: &Match,
    ) -> TypeResult {
        let enum_ = (*enum_type.enum_).borrow();

        let mut child_return_types: Vec<(String, Position, ReturnTypes)> = vec![];

        for case_block in &match_.case_blocks {
            let name = format!("case {}:{}", case_block.enum_name, case_block.variant_name);
            let position = case_block.position.clone();
            let variant_data = enum_
                .resolved()
                .variants
                .get(&case_block.variant_name)
                .unwrap();

            let case_stack = match self.check_case_block(stack.to_owned(), variant_data, case_block)
            {
                Ok(case_stack) => ReturnTypes::Sometimes(case_stack),
                Err(TypeError::DoesNotReturn) => ReturnTypes::Never,
                Err(err) => return Err(err),
            };

            child_return_types.push((name, position, case_stack));
        }

        for default_block in &match_.default_blocks {
            let name = "default".to_owned();
            let position = default_block.position.clone();

            let default_stack =
                match self.check_function_body(stack.to_owned(), &default_block.body) {
                    Ok(case_stack) => ReturnTypes::Sometimes(case_stack),
                    Err(TypeError::DoesNotReturn) => ReturnTypes::Never,
                    Err(err) => return Err(err),
                };

            child_return_types.push((name, position, default_stack));
        }

        // Find any case that returns, for easy comparison to other cases below.
        let returning_type = child_return_types
            .iter()
            .map(|(_, _, return_types)| return_types)
            .find(|return_types| matches!(return_types, ReturnTypes::Sometimes(_)));

        let Some(returning_type) = returning_type else {
            return does_not_return(); // All cases diverge
        };

        let ReturnTypes::Sometimes(first_child_stack) = returning_type else {
            unreachable!(); // filtered out above, but required by type system
        };

        for (_, _, child_return_type) in &child_return_types {
            if let ReturnTypes::Sometimes(child_stack) = child_return_type {
                if child_stack != first_child_stack {
                    return inconsistent_match_children(
                        match_.position.clone(),
                        child_return_types,
                    );
                }
            }
        }

        Ok(first_child_stack.clone())
    }

    fn check_case_block(
        &mut self,
        mut stack: Vec<Type>,
        variant_data: &Vec<Type>,
        case_block: &CaseBlock,
    ) -> TypeResult {
        if case_block.variables.is_empty() {
            stack.extend(variant_data.clone());
            return self.check_function_body(stack, &case_block.body);
        }

        if case_block.variables.len() != variant_data.len() {
            return unexpected_case_variable_count(
                case_block.position.clone(),
                case_block.enum_name.clone(),
                case_block.variant_name.clone(),
                variant_data.len(),
                case_block.variables.len(),
            );
        }

        for (variable, type_) in zip(&case_block.variables, variant_data) {
            let var_name = variable.name.clone();

            let local_variable = LocalVariable {
                name: var_name.clone(),
                type_: type_.clone(),
                position: variable.position.clone(),
            };

            self.check_variable_name_availability(&local_variable)?;

            self.local_variables.insert(var_name, local_variable);
        }

        let case_block_result = self.check_function_body(stack, &case_block.body);

        for variable in &case_block.variables {
            self.local_variables.remove(&variable.name);
        }

        case_block_result
    }

    fn check_call_enum_constructor(
        &self,
        stack: Vec<Type>,
        call: &CallEnumConstructor,
    ) -> TypeResult {
        let enum_ctor = &*call.enum_constructor.borrow();
        let enum_ = &*enum_ctor.enum_.borrow();

        let found_param_count = call.type_parameters.len();
        let expected_param_count = enum_.resolved().type_parameters.len();

        if found_param_count != expected_param_count {
            return parameter_count_error(
                call.position.clone(),
                found_param_count,
                expected_param_count,
            );
        }

        let type_parameters = enum_.parameter_mapping(&call.type_parameters);

        let enum_type_ = Type::Enum(EnumType {
            enum_: enum_ctor.enum_.clone(),
            parameters: call.type_parameters.clone(),
        });

        let argument_types: Vec<_> = enum_ctor
            .data()
            .iter()
            .map(|type_| CallChecker::apply_type_params(type_, &type_parameters))
            .clone()
            .collect();

        let checker = CallChecker {
            type_params: HashMap::new(),
            argument_types,
            return_types: ReturnTypes::Sometimes(vec![enum_type_]),
            name: enum_ctor.name(),
            position: call.position.clone(),
            stack,
        };

        checker.check()
    }

    fn check_call(&self, mut stack: Vec<Type>, call: &Call) -> TypeResult {
        let Some(top_type) = stack.pop() else {
            return call_stack_underflow(call.position.clone(), stack);
        };

        let Type::FunctionPointer(function_pointer) = top_type else {
            return call_non_function(call.position.clone(), top_type);
        };

        let checker = CallChecker {
            name: "function pointer".to_owned(),
            position: call.position.clone(),
            argument_types: function_pointer.argument_types,
            return_types: function_pointer.return_types,
            stack,
            type_params: HashMap::new(),
        };

        checker.check()
    }
}

use std::{collections::HashMap, iter::zip};

use super::errors::{does_not_return, stack_error, TypeResult};
use crate::{
    common::position::Position,
    cross_referencer::types::identifiable::{EnumType, Function, ReturnTypes, StructType, Type},
    type_checker::errors::stack_underflow,
};

pub struct FunctionCallChecker<'a> {
    position: Position,
    stack: Vec<Type>,
    function: &'a Function,
    type_params: HashMap<String, Type>,
}

impl<'a> FunctionCallChecker<'a> {
    pub fn new(position: Position, stack: Vec<Type>, function: &'a Function) -> Self {
        Self {
            position,
            stack,
            function,
            type_params: HashMap::new(),
        }
    }

    pub fn check(mut self) -> TypeResult {
        let signature = self.function.signature();
        let func_arg_types = signature.argument_types();

        let stack_before = self.stack.clone();

        if func_arg_types.len() > self.stack.len() {
            let func_name = self.function.name();
            return stack_underflow(self.position, func_name, stack_before, func_arg_types);
        }

        let func_return_types = match &signature.return_types {
            ReturnTypes::Sometimes(types) => types,
            ReturnTypes::Never => return does_not_return(),
        };

        let stack_size_after_call = self.stack.len() - func_arg_types.len();
        let stack_arg_types = self.stack.split_off(stack_size_after_call);

        for (func_arg, stack_arg) in zip(&func_arg_types, &stack_arg_types) {
            if !self.types_match(func_arg, stack_arg) {
                let func_name = self.function.name();
                return stack_error(self.position, func_name, stack_before, func_arg_types);
            }
        }

        let return_types = self.get_return_types(&func_return_types);
        self.stack.extend(return_types);

        Ok(self.stack)
    }

    // Returns whether rhs matches lhs, updating `self.type_params` in the process.
    fn types_match(&mut self, lhs: &Type, rhs: &Type) -> bool {
        use Type::*;

        match (lhs, rhs) {
            (FunctionPointer(lhs), FunctionPointer(rhs)) => lhs == rhs,
            (Struct(lhs), Struct(rhs)) => self.struct_types_match(lhs, rhs),
            (Enum(lhs), Enum(rhs)) => self.enum_types_match(lhs, rhs),
            (Parameter(lhs), _) => {
                if let Some(lhs) = self.type_params.get(&lhs.name) {
                    if lhs != rhs {
                        return false;
                    }
                };

                self.type_params.insert(lhs.name.clone(), rhs.clone());
                true
            }
            _ => false,
        }
    }

    fn struct_types_match(&mut self, lhs: &StructType, rhs: &StructType) -> bool {
        let lhs_key = (*lhs.struct_).borrow().key();
        let rhs_key = (*rhs.struct_).borrow().key();

        if lhs_key != rhs_key {
            return false;
        }

        lhs.parameters
            .iter()
            .zip(&rhs.parameters)
            .map(|(lhs, rhs)| self.types_match(lhs, rhs))
            .all(|x| x)
    }

    fn enum_types_match(&mut self, lhs: &EnumType, rhs: &EnumType) -> bool {
        let lhs_key = (*lhs.enum_).borrow().key();
        let rhs_key = (*rhs.enum_).borrow().key();

        if lhs_key != rhs_key {
            return false;
        }

        lhs.parameters
            .iter()
            .zip(&rhs.parameters)
            .map(|(lhs, rhs)| self.types_match(lhs, rhs))
            .all(|x| x)
    }

    fn get_return_types(&self, func_return_types: &Vec<Type>) -> Vec<Type> {
        let mut return_types = vec![];

        for type_ in func_return_types.iter().cloned() {
            let return_type = self.apply_type_params(type_.clone());
            return_types.push(return_type);
        }

        return_types
    }

    fn apply_type_params(&self, mut type_: Type) -> Type {
        match type_ {
            Type::Parameter(ref type_param) => {
                if let Some(found_type) = self.type_params.get(&type_param.name) {
                    return found_type.clone();
                }
            }
            Type::Struct(ref mut struct_) => {
                struct_.parameters = struct_
                    .parameters
                    .iter()
                    .cloned()
                    .map(|param| self.apply_type_params(param))
                    .collect();
            }
            _ => (),
        }

        type_
    }
}

use std::{collections::HashMap, iter::zip, path::PathBuf};

use super::errors::{does_not_return, stack_error, TypeResult};
use crate::{
    common::{position::Position, traits::HasPosition},
    cross_referencer::types::identifiable::{
        EnumType, Identifiable, InterfaceType, ResolvedInterfaceFunction, ReturnTypes, Struct,
        StructType, Type,
    },
    type_checker::errors::stack_underflow,
};

pub struct CallChecker<'a> {
    pub type_params: HashMap<String, Type>,
    pub argument_types: Vec<Type>,
    pub return_types: ReturnTypes,
    pub name: String,
    pub position: Position,
    pub stack: Vec<Type>,

    pub identifiables: &'a HashMap<(PathBuf, String), Identifiable>,
}

impl<'a> CallChecker<'a> {
    #[allow(clippy::result_large_err)] // TODO #239 Handle linter error for large error result
    pub fn check(self) -> TypeResult {
        let stack_before = self.stack.clone();

        if self.argument_types.len() > self.stack.len() {
            return stack_underflow(self.position, self.name, stack_before, self.argument_types);
        }

        let stack_size_after_call = self.stack.len() - self.argument_types.len();

        let mut stack = self.stack.clone();

        let stack_arg_types = stack.split_off(stack_size_after_call);

        let mut type_params = self.type_params.clone();

        for (func_arg, stack_arg) in zip(&self.argument_types, &stack_arg_types) {
            if !self.types_match(func_arg, stack_arg, &mut type_params) {
                let func_name = self.name;
                return stack_error(self.position, func_name, stack_before, self.argument_types);
            }
        }

        let return_types = match &self.return_types {
            ReturnTypes::Sometimes(types) => types.clone(),
            ReturnTypes::Never => return does_not_return(),
        };

        let return_types: Vec<_> = return_types
            .iter()
            .map(|type_| Self::apply_type_params(type_, &type_params))
            .collect();

        stack.extend(return_types);

        Ok(stack)
    }

    // Returns whether rhs matches lhs, updating `type_params` in the process.
    fn types_match(&self, lhs: &Type, rhs: &Type, type_params: &mut HashMap<String, Type>) -> bool {
        use Type::*;

        match (lhs, rhs) {
            (FunctionPointer(lhs), FunctionPointer(rhs)) => lhs == rhs,
            (Struct(lhs), Struct(rhs)) => self.struct_types_match(lhs, rhs, type_params),
            (Enum(lhs), Enum(rhs)) => self.enum_types_match(lhs, rhs, type_params),
            (Parameter(lhs), _) => {
                if let Some(lhs) = type_params.get(&lhs.name) {
                    match lhs {
                        Parameter(_) => (),
                        Interface(lhs) => return self.implements_interface(lhs, rhs),
                        _ => {
                            if lhs != rhs {
                                return false;
                            }
                        }
                    }
                };

                type_params.insert(lhs.name.clone(), rhs.clone());
                true
            }
            (Interface(lhs), Struct(rhs)) => self.struct_implements_interface(lhs, rhs),
            (Interface(_lhs), Enum(_rhs)) => todo!(), // TODO
            (Interface(lhs), Interface(rhs)) => self.interface_implements_interface(lhs, rhs),
            _ => false,
        }
    }

    fn struct_types_match(
        &self,
        lhs: &StructType,
        rhs: &StructType,
        type_params: &mut HashMap<String, Type>,
    ) -> bool {
        let lhs_key = (*lhs.struct_).borrow().key();
        let rhs_key = (*rhs.struct_).borrow().key();

        if lhs_key != rhs_key {
            return false;
        }

        lhs.parameters
            .iter()
            .zip(&rhs.parameters)
            .map(|(lhs, rhs)| self.types_match(lhs, rhs, type_params))
            .all(|x| x)
    }

    fn enum_types_match(
        &self,
        lhs: &EnumType,
        rhs: &EnumType,
        type_params: &mut HashMap<String, Type>,
    ) -> bool {
        let lhs_key = (*lhs.enum_).borrow().key();
        let rhs_key = (*rhs.enum_).borrow().key();

        if lhs_key != rhs_key {
            return false;
        }

        lhs.parameters
            .iter()
            .zip(&rhs.parameters)
            .map(|(lhs, rhs)| self.types_match(lhs, rhs, type_params))
            .all(|x| x)
    }

    pub fn implements_interface(&self, interface_type: &InterfaceType, type_: &Type) -> bool {
        match type_ {
            Type::Struct(struct_type) => {
                self.struct_implements_interface(interface_type, struct_type)
            }
            _ => todo!(), // TODO
        }
    }

    pub fn struct_implements_interface(
        &self,
        interface_type: &InterfaceType,
        struct_type: &StructType,
    ) -> bool {
        let interface = &*interface_type.interface.borrow();
        let struct_ = &*struct_type.struct_.borrow();

        for required_function in &interface.resolved().functions {
            if !self.struct_implements_interface_function(required_function, struct_) {
                return false;
            }
        }

        true
    }

    fn struct_implements_interface_function(
        &self,
        interface_function: &ResolvedInterfaceFunction,
        struct_: &Struct,
    ) -> bool {
        // TODO lookup in TypeChecker

        let key = (
            struct_.position().path.clone(),
            format!("{}:{}", struct_.name(), &interface_function.name),
        );

        let Some(identifiable) = self.identifiables.get(&key) else {
            return false;
        };

        let Identifiable::Function(function) = identifiable else {
            return false;
        };

        let function = &*function.borrow();

        if function.arguments().len() != interface_function.arguments.len() {
            return false;
        }

        for (interface_function_arg, function_arg) in
            zip(&interface_function.arguments, &function.arguments()[1..])
        {
            if !self.types_match(
                &interface_function_arg.type_,
                &function_arg.type_,
                &mut HashMap::new(),
            ) {
                return false;
            }
        }

        use ReturnTypes::*;

        match (&interface_function.return_types, function.return_types()) {
            (_, Never) => (),
            (Never, Sometimes(_)) => return false,
            (Sometimes(lhs), Sometimes(rhs)) => {
                if lhs != rhs {
                    return false;
                }
            }
        }

        true
    }

    fn interface_implements_interface(&self, lhs: &InterfaceType, rhs: &InterfaceType) -> bool {
        if lhs.interface.borrow().key() == rhs.interface.borrow().key() {
            return true;
        }

        // TODO find out if rhs is subset of rhs
        false
    }

    pub fn apply_type_params(type_: &Type, type_params: &HashMap<String, Type>) -> Type {
        match type_ {
            Type::Parameter(type_param) => {
                if let Some(found_type) = type_params.get(&type_param.name) {
                    return found_type.clone();
                }
                return Type::Parameter(type_param.clone());
            }
            Type::Struct(struct_) => {
                let mut struct_ = struct_.clone();

                struct_.parameters = struct_
                    .parameters
                    .iter()
                    .map(|param| Self::apply_type_params(param, type_params))
                    .collect();

                return Type::Struct(struct_);
            }
            Type::Enum(enum_) => {
                let mut enum_ = enum_.clone();

                enum_.parameters = enum_
                    .parameters
                    .iter()
                    .map(|param| Self::apply_type_params(param, type_params))
                    .collect();

                return Type::Enum(enum_);
            }
            _ => (),
        }

        type_.clone()
    }
}

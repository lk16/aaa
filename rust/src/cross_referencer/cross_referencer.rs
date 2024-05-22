#![allow(dead_code)] // TODO

use std::{
    cell::RefCell,
    collections::{hash_map::Entry as HashMapEntry, HashMap, HashSet},
    fmt::Debug,
    path::PathBuf,
    rc::Rc,
};

use super::{
    errors::{
        CollidingIdentifiables, CrossReferencerError, CyclicDependency, ImportNotFound,
        IndirectImport, InvalidArgument, UnexpectedBuiltin, UnknownIdentifiable,
    },
    types::{
        Argument, Assignment, Boolean, Branch, Call, CallArgument, CallByName, CallEnum,
        CallEnumConstructor, CallFunction, CallLocalVariable, CallStruct, CaseBlock, Char,
        DefaultBlock, Enum, Foreach, Function, FunctionBody, FunctionBodyItem, FunctionSignature,
        GetField, Identifiable, Import, Integer, Match, ParsedString, ResolvedEnum, ResolvedStruct,
        Return, ReturnTypes, Struct, Type, TypeParameter, Use, Variable,
    },
};
use crate::{
    common::position::Position,
    cross_referencer::{
        errors::InvalidReturnType,
        types::{FunctionType, SetField, While},
    },
    parser::types::{self as parsed, SourceFile},
};

pub fn cross_reference(
    parsed_files: HashMap<PathBuf, parsed::SourceFile>,
    entrypoint_path: PathBuf,
    builtins_path: PathBuf,
    current_dir: PathBuf,
) -> Result<Output, Vec<CrossReferencerError>> {
    let cross_referencer =
        CrossReferencer::new(parsed_files, entrypoint_path, builtins_path, current_dir);
    cross_referencer.cross_reference()
}

pub struct Output {
    pub identifiables: HashMap<(PathBuf, String), Identifiable>,
}

impl Debug for Output {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Output with {} identifiables", self.identifiables.len())
    }
}

pub struct CrossReferencer {
    parsed_files: HashMap<PathBuf, parsed::SourceFile>,
    entrypoint_path: PathBuf,
    builtins_path: PathBuf,
    current_dir: PathBuf,
    cross_referenced_files: HashSet<PathBuf>,
    dependency_stack: Vec<PathBuf>,
    identifiables: HashMap<(PathBuf, String), Identifiable>,
    errors: Vec<CrossReferencerError>,
}

impl CrossReferencer {
    fn new(
        parsed_files: HashMap<PathBuf, parsed::SourceFile>,
        entrypoint_path: PathBuf,
        builtins_path: PathBuf,
        current_dir: PathBuf,
    ) -> Self {
        Self {
            parsed_files,
            entrypoint_path,
            builtins_path,
            current_dir,
            cross_referenced_files: HashSet::new(),
            dependency_stack: vec![],
            identifiables: HashMap::new(),
            errors: vec![],
        }
    }

    fn cross_reference(mut self) -> Result<Output, Vec<CrossReferencerError>> {
        let entrypoint_path = self.entrypoint_path.clone();

        if let Err(error) = self.cross_reference_file_with_dependencies(&entrypoint_path) {
            self.errors.push(error);
        }

        if self.errors.len() > 0 {
            return Err(self.errors);
        }

        Ok(Output {
            identifiables: self.identifiables,
        })
    }

    fn cross_reference_file_with_dependencies(
        &mut self,
        path: &PathBuf,
    ) -> Result<(), CrossReferencerError> {
        if self.dependency_stack.contains(&path) {
            let mut dependencies = self.dependency_stack.clone();
            dependencies.push(path.clone());

            let error = CyclicDependency { dependencies };
            return Err(error.into());
        }

        self.dependency_stack.push(path.clone());

        for dependency in self.get_remaining_dependencies(path) {
            self.cross_reference_file_with_dependencies(&dependency)?;
        }

        if !self.cross_referenced_files.contains(path) {
            self.cross_reference_file(path);
        }

        self.dependency_stack.pop();
        self.cross_referenced_files.insert(path.clone());

        Ok(())
    }

    fn get_remaining_dependencies(&self, path: &PathBuf) -> Vec<PathBuf> {
        if *path == self.builtins_path {
            return vec![];
        }

        let mut dependencies = self
            .parsed_files
            .get(path)
            .unwrap()
            .dependencies(&self.current_dir);

        dependencies.push(self.builtins_path.clone());

        dependencies
    }

    fn cross_reference_file(&mut self, path: &PathBuf) {
        let source_file = self.parsed_files.get(path).unwrap();

        let indentifiables = self.load_file(source_file);

        for identifiable in indentifiables.iter() {
            if identifiable.is_builtin() && identifiable.key().0 != self.builtins_path {
                let error = UnexpectedBuiltin {
                    position: identifiable.position(),
                    identifiable: identifiable.clone(),
                };
                self.errors.push(error.into());
            }
        }

        for identifiable in indentifiables.iter() {
            let key = identifiable.key();

            match self.identifiables.entry(key) {
                HashMapEntry::Vacant(entry) => {
                    entry.insert(identifiable.clone());
                }
                HashMapEntry::Occupied(entry) => {
                    let error = CollidingIdentifiables {
                        identifiables: [entry.get().clone(), identifiable.clone()],
                    };
                    self.errors.push(error.into());
                }
            };
        }

        let mut structs = vec![];
        let mut enums = vec![];
        let mut functions = vec![];
        let mut imports = vec![];

        for identifiable in indentifiables.iter() {
            match identifiable {
                Identifiable::Struct(struct_) => structs.push(struct_.clone()),
                Identifiable::Enum(enum_) => enums.push(enum_.clone()),
                Identifiable::Function(function) => functions.push(function.clone()),
                Identifiable::Import(import) => imports.push(import.clone()),
                _ => (),
            }
        }

        for import in imports.iter().cloned() {
            self.errors.extend(self.resolve_import(import));
        }

        for struct_ in structs.iter().cloned() {
            if let Err(error) = self.resolve_struct(struct_) {
                self.errors.push(error);
            }
        }

        for enum_ in enums.iter().cloned() {
            if let Err(error) = self.resolve_enum(enum_) {
                self.errors.push(error);
            }
        }

        for function in functions.iter().cloned() {
            if let Err(error) = self.resolve_function_signature(function) {
                self.errors.push(error);
            }
        }

        for function in functions.iter().cloned() {
            if let Err(error) = self.resolve_function(function) {
                self.errors.push(error);
            }
        }
    }

    fn load_file(&self, source_file: &SourceFile) -> Vec<Identifiable> {
        let mut identifiables = vec![];

        identifiables.extend(Self::load_structs(&source_file.structs));
        identifiables.extend(Self::load_enums(&source_file.enums));
        identifiables.extend(Self::load_functions(&source_file.functions));
        identifiables.extend(Self::load_imports(&source_file.imports));

        identifiables
    }

    fn load_structs(parsed_structs: &Vec<parsed::Struct>) -> Vec<Identifiable> {
        parsed_structs
            .iter()
            .cloned()
            .map(|parsed| parsed.into())
            .collect()
    }

    fn load_enums(parsed_enums: &Vec<parsed::Enum>) -> Vec<Identifiable> {
        let mut identifiables = vec![];

        for parsed_enum in parsed_enums.iter() {
            let enum_: Identifiable = parsed_enum.clone().into();
            identifiables.push(enum_.clone());

            let enum_rc = match enum_ {
                Identifiable::Enum(enum_rc) => enum_rc,
                _ => unreachable!(),
            };

            for parsed_variant in parsed_enum.variants.iter().cloned() {
                let tuple = (enum_rc.clone(), parsed_variant);
                identifiables.push(tuple.into());
            }
        }

        identifiables
    }

    fn load_functions(parsed_functions: &Vec<parsed::Function>) -> Vec<Identifiable> {
        parsed_functions
            .iter()
            .cloned()
            .map(|parsed_function| parsed_function.into())
            .collect()
    }

    fn load_imports(parsed_imports: &Vec<parsed::Import>) -> Vec<Identifiable> {
        let mut imports = vec![];

        for parsed_import in parsed_imports.iter() {
            for parsed_item in parsed_import.items.iter() {
                let tuple = (parsed_import.clone(), parsed_item.clone());
                imports.push(tuple.into());
            }
        }

        imports
    }

    fn resolve_import(&self, import_rc: Rc<RefCell<Import>>) -> Vec<CrossReferencerError> {
        let mut errors = vec![];

        let target = {
            let import = import_rc.borrow();
            let target_key = import.target_key();

            let target = match self.identifiables.get(&target_key) {
                Some(identifiable) => identifiable,
                None => {
                    let error = ImportNotFound {
                        position: import.position(),
                    };
                    errors.push(error.into());
                    return errors;
                }
            };

            if let Identifiable::Import(_) = target {
                let error = IndirectImport {
                    position: import.parsed_item.position.clone(),
                };
                errors.push(error.into());
                return errors;
            }

            target
        };

        (*import_rc).borrow_mut().resolved = Some(target.clone());

        errors
    }

    fn resolve_struct(&self, struct_rc: Rc<RefCell<Struct>>) -> Result<(), CrossReferencerError> {
        let type_parameters = self.resolve_struct_parameters(struct_rc.clone())?;
        let fields = self.resolve_struct_fields(struct_rc.clone(), &type_parameters)?;

        (*struct_rc).borrow_mut().resolved = Some(ResolvedStruct {
            fields,
            type_parameters,
        });

        Ok(())
    }

    fn resolve_struct_parameters(
        &self,
        struct_rc: Rc<RefCell<Struct>>,
    ) -> Result<HashMap<String, Type>, CrossReferencerError> {
        let mut resolved_parameters = HashMap::new();
        let struct_ = struct_rc.borrow();

        for parsed_parameter in struct_.parsed.parameters.iter() {
            let parameter = TypeParameter::from_parsed(&parsed_parameter);
            let key = (struct_.position().path, parameter.name.clone());

            if let Some(identifier) = self.identifiables.get(&key) {
                let error = CollidingIdentifiables {
                    identifiables: [Identifiable::Struct(struct_rc.clone()), identifier.clone()],
                };
                return Err(error.into());
            }

            let name = parameter.name.clone();
            let type_ = Type::Parameter(parameter);
            resolved_parameters.insert(name, type_);
        }

        Ok(resolved_parameters)
    }

    fn resolve_struct_fields(
        &self,
        struct_rc: Rc<RefCell<Struct>>,
        type_parameters: &HashMap<String, Type>,
    ) -> Result<HashMap<String, Type>, CrossReferencerError> {
        let struct_ = struct_rc.borrow();
        let mut fields = HashMap::new();

        if let Some(parsed_fields) = &struct_.parsed.fields {
            for parsed_field in parsed_fields {
                let name = parsed_field.name.value.clone();
                let field = self.resolve_type(&parsed_field.type_, &type_parameters)?;
                fields.insert(name, field);
            }
        }

        Ok(fields)
    }

    fn resolve_type(
        &self,
        parsed: &parsed::Type,
        type_parameters: &HashMap<String, Type>,
    ) -> Result<Type, CrossReferencerError> {
        match parsed {
            parsed::Type::Function(function_type) => {
                self.resolve_function_pointer_type(function_type, type_parameters)
            }
            parsed::Type::Regular(regular_type) => {
                self.resolve_regular_type(regular_type, type_parameters)
            }
        }
    }

    fn resolve_function_pointer_type(
        &self,
        parsed: &parsed::FunctionType,
        _type_parameters: &HashMap<String, Type>,
    ) -> Result<Type, CrossReferencerError> {
        let empty_hashmap = HashMap::new();
        let mut argument_types = vec![];

        for parsed_arg_type in parsed.argument_types.iter() {
            let argument_type = self.resolve_type(parsed_arg_type, &empty_hashmap)?;
            argument_types.push(argument_type);
        }

        let return_types = match &parsed.return_types {
            parsed::ReturnTypes::Never => ReturnTypes::Never,
            parsed::ReturnTypes::Sometimes(parsed_return_types) => {
                let mut return_types = vec![];

                for parsed_return_type in parsed_return_types.iter() {
                    let return_type = self.resolve_type(parsed_return_type, &empty_hashmap)?;
                    return_types.push(return_type);
                }

                ReturnTypes::Sometimes(return_types)
            }
        };

        let type_ = Type::FunctionPointer {
            argument_types,
            return_types,
        };

        Ok(type_)
    }

    fn resolve_regular_type(
        &self,
        parsed: &parsed::RegularType,
        type_parameters: &HashMap<String, Type>,
    ) -> Result<Type, CrossReferencerError> {
        let type_name = &parsed.name.value;

        if let Some(type_) = type_parameters.get(type_name) {
            return Ok(type_.clone());
        }

        let identifiable =
            self.get_identifiable(parsed.position.clone(), parsed.name.value.clone())?;

        let parameters = self.resolve_type_parameters(parsed, type_parameters)?;

        let type_ = match identifiable {
            Identifiable::Enum(enum_) => Type::Enum { enum_, parameters },
            Identifiable::Struct(struct_) => Type::Struct {
                struct_,
                parameters,
            },
            _ => unreachable!(),
        };

        Ok(type_)
    }

    fn resolve_type_parameters(
        &self,
        parsed: &parsed::RegularType,
        type_parameters: &HashMap<String, Type>,
    ) -> Result<Vec<Type>, CrossReferencerError> {
        parsed
            .parameters
            .iter()
            .map(|parsed_param| self.resolve_type_parameter(parsed_param, type_parameters))
            .collect()
    }

    fn resolve_type_parameter(
        &self,
        parsed: &parsed::Type,
        type_parameters: &HashMap<String, Type>,
    ) -> Result<Type, CrossReferencerError> {
        let regular_type = match parsed {
            parsed::Type::Function(function) => {
                return self.resolve_function_pointer_type(function, type_parameters)
            }
            parsed::Type::Regular(regular_type) => regular_type,
        };

        if let Some(param_type) = type_parameters.get(&regular_type.name.value) {
            return Ok(param_type.clone());
        }

        let identifiable = self.get_identifiable(
            regular_type.position.clone(),
            regular_type.name.value.clone(),
        )?;

        let parameters = self.resolve_type_parameters(regular_type, type_parameters)?;

        let type_ = match identifiable {
            Identifiable::Enum(enum_) => Type::Enum { enum_, parameters },
            Identifiable::Struct(struct_) => Type::Struct {
                struct_,
                parameters,
            },
            _ => {
                let error = InvalidArgument {
                    position: parsed.position(),
                    identifiable,
                };
                return Err(error.into());
            }
        };

        Ok(type_)
    }

    fn get_identifiable(
        &self,
        position: Position,
        name: String,
    ) -> Result<Identifiable, CrossReferencerError> {
        let builtins_key = &(self.builtins_path.clone(), name.clone());
        let key = (position.path.clone(), name.clone());

        let mut identifiable = self.identifiables.get(&builtins_key);

        if let None = identifiable {
            identifiable = self.identifiables.get(&key);
        }

        let identifiable = match identifiable {
            Some(identifiable) => identifiable.clone(),
            None => return self.get_identifiable_with_type_name(position, name),
        };

        if let Identifiable::Import(import) = identifiable {
            let import = &*import.borrow();

            match &import.resolved {
                None => {
                    let error = UnknownIdentifiable { name, position };
                    return Err(error.into());
                }
                Some(imported) => return Ok(imported.clone()),
            }
        }

        Ok(identifiable)
    }

    fn get_identifiable_with_type_name(
        &self,
        position: Position,
        name: String,
    ) -> Result<Identifiable, CrossReferencerError> {
        if let Some((type_name, _)) = name.split_once(":") {
            let type_key = (position.path.clone(), type_name.to_string());

            if let Some(Identifiable::Import(type_import_rc)) = self.identifiables.get(&type_key) {
                let type_import = type_import_rc.borrow();
                let type_path = type_import
                    .parsed_import
                    .get_source_path(&std::env::current_dir().unwrap());

                let type_position = Position {
                    path: type_path,
                    column: 0,
                    line: 0,
                };

                return self.get_identifiable(type_position, name);
            }
        }

        let error = UnknownIdentifiable { name, position };
        Err(error.into())
    }

    fn resolve_enum(&self, enum_: Rc<RefCell<Enum>>) -> Result<(), CrossReferencerError> {
        let type_parameters = self.resolve_enum_parameters(enum_.clone())?;
        let variants = self.resolve_enum_variants(enum_.clone(), &type_parameters)?;

        (*enum_).borrow_mut().resolved = Some(ResolvedEnum {
            type_parameters,
            variants,
        });

        Ok(())
    }

    fn resolve_enum_parameters(
        &self,
        enum_rc: Rc<RefCell<Enum>>,
    ) -> Result<HashMap<String, Type>, CrossReferencerError> {
        let mut resolved_parameters = HashMap::new();
        let enum_ = enum_rc.borrow();

        for parsed_parameter in enum_.parsed.parameters.iter() {
            let parameter = TypeParameter::from_parsed(&parsed_parameter);
            let key = (enum_.position().path, parameter.name.clone());

            if let Some(identifier) = self.identifiables.get(&key) {
                let error = CollidingIdentifiables {
                    identifiables: [Identifiable::Enum(enum_rc.clone()), identifier.clone()],
                };

                return Err(error.into());
            }

            let name = parameter.name.clone();
            let type_ = Type::Parameter(parameter);
            resolved_parameters.insert(name, type_);
        }

        Ok(resolved_parameters)
    }

    fn resolve_enum_variants(
        &self,
        enum_rc: Rc<RefCell<Enum>>,
        type_parameters: &HashMap<String, Type>,
    ) -> Result<HashMap<String, Vec<Type>>, CrossReferencerError> {
        let enum_ = enum_rc.borrow();
        let mut variants = HashMap::new();

        for parsed_variant in enum_.parsed.variants.iter() {
            let name = parsed_variant.name.value.clone();
            let mut data = vec![];

            for unresolved_data_item in parsed_variant.data.iter() {
                let data_item = self.resolve_type(&unresolved_data_item, &type_parameters)?;
                data.push(data_item);
            }
            variants.insert(name, data);
        }

        Ok(variants)
    }

    fn resolve_function_signature(
        &self,
        function_rc: Rc<RefCell<Function>>,
    ) -> Result<(), CrossReferencerError> {
        let type_parameters = self.resolve_function_parameters(function_rc.clone())?;
        let arguments = self.resolve_function_arguments(function_rc.clone(), &type_parameters)?;
        let return_types =
            self.resolve_function_return_types(function_rc.clone(), &type_parameters)?;

        (*function_rc).borrow_mut().resolved_signature = Some(FunctionSignature {
            type_parameters,
            arguments,
            return_types,
        });

        Ok(())
    }

    fn resolve_function_parameters(
        &self,
        function_rc: Rc<RefCell<Function>>,
    ) -> Result<HashMap<String, Type>, CrossReferencerError> {
        let mut resolved_parameters = HashMap::new();
        let function = function_rc.borrow();

        let parsed_parameters = match &function.parsed.name {
            parsed::FunctionName::Free(free) => &free.parameters,
            parsed::FunctionName::Member(member) => &member.parameters,
        };

        for parsed_parameter in parsed_parameters.iter() {
            let parameter = TypeParameter::from_parsed(&parsed_parameter);
            let key = (function.position().path, parameter.name.clone());

            if let Some(identifier) = self.identifiables.get(&key) {
                let error = CollidingIdentifiables {
                    identifiables: [
                        Identifiable::Function(function_rc.clone()),
                        identifier.clone(),
                    ],
                };
                return Err(error.into());
            }

            let name = parameter.name.clone();
            let type_ = Type::Parameter(parameter);
            resolved_parameters.insert(name, type_);
        }

        Ok(resolved_parameters)
    }

    fn resolve_function_arguments(
        &self,
        function_rc: Rc<RefCell<Function>>,
        type_parameters: &HashMap<String, Type>,
    ) -> Result<Vec<Argument>, CrossReferencerError> {
        let function = function_rc.borrow();

        function
            .parsed
            .arguments
            .iter()
            .map(|parsed| self.resolve_function_argument(parsed, type_parameters))
            .collect()
    }

    fn resolve_function_return_types(
        &self,
        function_rc: Rc<RefCell<Function>>,
        type_parameters: &HashMap<String, Type>,
    ) -> Result<ReturnTypes, CrossReferencerError> {
        let function = function_rc.borrow();

        let types = match &function.parsed.return_types {
            parsed::ReturnTypes::Never => return Ok(ReturnTypes::Never),
            parsed::ReturnTypes::Sometimes(types) => types,
        };

        let types = types
            .iter()
            .map(|type_| self.resolve_function_return_type(type_, type_parameters))
            .collect::<Result<_, _>>()?;

        Ok(ReturnTypes::Sometimes(types))
    }

    fn resolve_function_argument(
        &self,
        parsed: &parsed::Argument,
        type_parameters: &HashMap<String, Type>,
    ) -> Result<Argument, CrossReferencerError> {
        let result = self.resolve_function_return_type(&parsed.type_, type_parameters);

        let type_ = match result {
            Ok(type_) => type_,
            Err(CrossReferencerError::InvalidReturnType(invalid_return_type)) => {
                let error = InvalidArgument {
                    identifiable: invalid_return_type.identifiable,
                    position: parsed.position.clone(),
                };
                return Err(error.into());
            }
            Err(error) => return Err(error),
        };

        let name = parsed.name.value.clone();
        Ok(Argument { type_, name })
    }

    fn resolve_function_return_type_function_pointer(
        &self,
        parsed: &parsed::FunctionType,
        type_parameters: &HashMap<String, Type>,
    ) -> Result<Type, CrossReferencerError> {
        let argument_types = parsed
            .argument_types
            .iter()
            .map(|arg_type| self.resolve_function_return_type(arg_type, type_parameters))
            .collect::<Result<_, _>>()?;

        let return_types = match &parsed.return_types {
            parsed::ReturnTypes::Never => ReturnTypes::Never,
            parsed::ReturnTypes::Sometimes(types) => ReturnTypes::Sometimes(
                types
                    .iter()
                    .map(|arg_type| self.resolve_function_return_type(arg_type, type_parameters))
                    .collect::<Result<_, _>>()?,
            ),
        };

        return Ok(Type::FunctionPointer {
            argument_types,
            return_types,
        });
    }

    fn resolve_function_return_type(
        &self,
        parsed: &parsed::Type,
        type_parameters: &HashMap<String, Type>,
    ) -> Result<Type, CrossReferencerError> {
        let regular_type = match parsed {
            parsed::Type::Function(function_type) => {
                return self
                    .resolve_function_return_type_function_pointer(function_type, type_parameters)
            }
            parsed::Type::Regular(type_) => type_,
        };

        let type_name = regular_type.name.value.clone();

        if let Some(type_) = type_parameters.get(&type_name) {
            return Ok(type_.clone());
        }

        let position = regular_type.position.clone();
        let identifiable = self.get_identifiable(position, type_name)?;

        let parameters = self.lookup_function_parameters(type_parameters, parsed)?;

        let type_ = match identifiable {
            Identifiable::Enum(enum_rc) => Type::Enum {
                enum_: enum_rc,
                parameters,
            },
            Identifiable::Struct(struct_rc) => Type::Struct {
                struct_: struct_rc,
                parameters,
            },
            identifiable => {
                let error = InvalidReturnType {
                    position: parsed.position(),
                    identifiable,
                };
                return Err(error.into());
            }
        };

        Ok(type_)
    }

    fn lookup_function_parameters(
        &self,
        type_parameters: &HashMap<String, Type>,
        parsed_type: &parsed::Type,
    ) -> Result<Vec<Type>, CrossReferencerError> {
        let parsed_parameters = match parsed_type {
            parsed::Type::Function(_) => &vec![],
            parsed::Type::Regular(regular_type) => &regular_type.parameters,
        };

        parsed_parameters
            .iter()
            .map(|parsed_param| self.lookup_function_parameter(type_parameters, parsed_param))
            .collect()
    }

    fn lookup_function_parameter(
        &self,
        type_parameters: &HashMap<String, Type>,
        parsed_type_parameter: &parsed::Type,
    ) -> Result<Type, CrossReferencerError> {
        let regular_parsed_type_parameter = match parsed_type_parameter {
            parsed::Type::Function(_) => todo!(),
            parsed::Type::Regular(regular_type) => regular_type,
        };

        let type_ = match type_parameters.get(&regular_parsed_type_parameter.name.value) {
            None => {
                let identifiable = self.get_identifiable(
                    regular_parsed_type_parameter.position.clone(),
                    regular_parsed_type_parameter.name.value.clone(),
                )?;

                let parameters =
                    self.lookup_function_parameters(type_parameters, parsed_type_parameter)?;

                match identifiable {
                    Identifiable::Struct(struct_) => Type::Struct {
                        struct_,
                        parameters,
                    },
                    Identifiable::Enum(enum_) => Type::Enum { enum_, parameters },
                    _ => todo!(), // InvalidType
                }
            }
            Some(_type_) => Type::Parameter(TypeParameter {
                position: regular_parsed_type_parameter.position.clone(),
                name: regular_parsed_type_parameter.name.value.clone(),
            }),
        };

        Ok(type_)
    }

    fn resolve_function(
        &self,
        function_rc: Rc<RefCell<Function>>,
    ) -> Result<(), CrossReferencerError> {
        let resolved_body = {
            let function = function_rc.borrow();

            if function.resolved_signature.is_none() {
                // Something went wrong earlier.
                return Ok(());
            }

            match &function.parsed.body {
                None => None,
                Some(parsed_body) => {
                    let resolved_body = self.resolve_function_body(&function, parsed_body)?;
                    Some(resolved_body)
                }
            }
        };

        (*function_rc).borrow_mut().resolved_body = resolved_body;

        Ok(())
    }

    fn resolve_function_body(
        &self,
        function: &Function,
        parsed_body: &parsed::FunctionBody,
    ) -> Result<FunctionBody, CrossReferencerError> {
        let mut resolver = FunctionBodyResolver::new(self, function);

        resolver.resolve_function_body(parsed_body)
    }
}

struct FunctionBodyResolver<'a> {
    cross_referencer: &'a CrossReferencer,
    function: &'a Function,
    local_variables: HashSet<String>,
}

impl<'a> FunctionBodyResolver<'a> {
    fn new(cross_referencer: &'a CrossReferencer, function: &'a Function) -> Self {
        Self {
            cross_referencer,
            function,
            local_variables: HashSet::new(),
        }
    }

    fn resolve_function_body(
        &mut self,
        parsed_body: &parsed::FunctionBody,
    ) -> Result<FunctionBody, CrossReferencerError> {
        let resolved_items = parsed_body
            .items
            .iter()
            .map(|item| self.resolve_function_body_item(item))
            .collect::<Result<_, _>>()?;

        Ok(FunctionBody {
            items: resolved_items,
            position: parsed_body.position.clone(),
        })
    }

    fn resolve_function_body_item(
        &mut self,
        parsed: &parsed::FunctionBodyItem,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        // NOTE: local shorthand for readability
        use parsed::FunctionBodyItem as ParsedItem;

        match parsed {
            ParsedItem::Assignment(assignment) => self.resolve_assignment(assignment),
            ParsedItem::Boolean(boolean) => Self::resolve_boolean(boolean),
            ParsedItem::Branch(branch) => self.resolve_branch(branch),
            ParsedItem::CallByPointer(call_by_pointer) => {
                Self::resolve_call_by_pointer(call_by_pointer)
            }
            ParsedItem::Char(char) => Self::resolve_char(char),
            ParsedItem::Foreach(foreach) => self.resolve_foreach(foreach),
            ParsedItem::FunctionCall(call) => self.resolve_function_call(call),
            ParsedItem::FunctionType(type_) => self.resolve_function_type(type_),
            ParsedItem::GetField(get_field) => self.resolve_get_field(get_field),
            ParsedItem::CallByName(call_by_name) => self.resolve_call_by_name(call_by_name),
            ParsedItem::Integer(integer) => Self::resolve_integer(integer),
            ParsedItem::Match(match_) => self.resolve_match(match_),
            ParsedItem::Return(return_) => self.resolve_return(return_),
            ParsedItem::SetField(set_field) => self.resolve_set_field(set_field),
            ParsedItem::String(string) => Self::resolve_string(string),
            ParsedItem::Use(use_) => self.resolve_use(use_),
            ParsedItem::While(while_) => self.resolve_while(while_),
        }
    }

    fn resolve_assignment(
        &mut self,
        parsed: &parsed::Assignment,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let variables = parsed
            .variables
            .iter()
            .cloned()
            .map(|var| Variable::from(var))
            .collect();

        let assignment = Assignment {
            position: parsed.position.clone(),
            variables,
            body: self.resolve_function_body(&parsed.body)?,
        };

        Ok(FunctionBodyItem::Assignment(assignment))
    }

    fn resolve_branch(
        &mut self,
        parsed: &parsed::Branch,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let else_body = match &parsed.else_body {
            Some(else_body) => Some(self.resolve_function_body(else_body)?),
            None => None,
        };

        let branch = Branch {
            position: parsed.position.clone(),
            condition: self.resolve_function_body(&parsed.condition)?,
            if_body: self.resolve_function_body(&parsed.if_body)?,
            else_body,
        };

        Ok(FunctionBodyItem::Branch(branch))
    }

    fn resolve_boolean(parsed: &parsed::Boolean) -> Result<FunctionBodyItem, CrossReferencerError> {
        let boolean = Boolean {
            position: parsed.position.clone(),
            value: parsed.value,
        };

        Ok(FunctionBodyItem::Boolean(boolean))
    }

    fn resolve_call_by_pointer(
        parsed: &parsed::CallByPointer,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let call = Call {
            position: parsed.position.clone(),
        };

        Ok(FunctionBodyItem::Call(call))
    }

    fn resolve_char(parsed: &parsed::Char) -> Result<FunctionBodyItem, CrossReferencerError> {
        let char_ = Char {
            position: parsed.position.clone(),
            value: parsed.value,
        };

        Ok(FunctionBodyItem::Char(char_))
    }

    fn resolve_foreach(
        &mut self,
        parsed: &parsed::Foreach,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let foreach = Foreach {
            position: parsed.position.clone(),
            body: self.resolve_function_body(&parsed.body)?,
        };

        Ok(FunctionBodyItem::Foreach(foreach))
    }

    fn resolve_function_call(
        &mut self,
        parsed: &parsed::FunctionCall,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let (name, position) = match parsed {
            parsed::FunctionCall::Free(free) => (free.name.value.clone(), free.position.clone()),
            parsed::FunctionCall::Member(member) => (
                format!("{}:{}", member.type_name.value, member.func_name.value),
                member.position.clone(),
            ),
        };

        if self.function.has_argument(&name) {
            return Ok(FunctionBodyItem::CallArgument(CallArgument {
                name,
                position,
            }));
        }

        if let Some(_) = self.local_variables.get(&name) {
            return Ok(FunctionBodyItem::CallLocalVariable(CallLocalVariable {
                name,
                position,
            }));
        }

        let identifiable = self.cross_referencer.get_identifiable(position, name)?;

        let type_parameters = match &self.function.resolved_signature {
            Some(signature) => &signature.type_parameters,
            None => unreachable!(),
        };

        let call_parameters = match parsed {
            parsed::FunctionCall::Free(free) => &free.parameters,
            parsed::FunctionCall::Member(member) => &member.parameters,
        };

        let _parameters = call_parameters.iter().map(|param| {
            self.cross_referencer
                .resolve_type_parameter(param, &type_parameters)
        });

        match identifiable {
            Identifiable::Import(_) => unreachable!(),
            Identifiable::Function(function_rc) => {
                return Ok(FunctionBodyItem::CallFunction(CallFunction {
                    function: function_rc.clone(),
                    type_parameters: type_parameters.clone(),
                    position: function_rc.borrow().position(),
                }))
            }
            Identifiable::Enum(enum_rc) => {
                return Ok(FunctionBodyItem::CallEnum(CallEnum {
                    function: enum_rc.clone(),
                    type_parameters: type_parameters.clone(),
                    position: enum_rc.borrow().position(),
                }))
            }
            Identifiable::Struct(struct_rc) => {
                return Ok(FunctionBodyItem::CallStruct(CallStruct {
                    function: struct_rc.clone(),
                    type_parameters: type_parameters.clone(),
                    position: struct_rc.borrow().position(),
                }))
            }
            Identifiable::EnumConstructor(enum_ctor) => {
                return Ok(FunctionBodyItem::CallEnumConstructor(CallEnumConstructor {
                    enum_constructor: enum_ctor.clone(),
                    type_parameters: type_parameters.clone(),
                    position: enum_ctor.borrow().position(),
                }));
            }
        }
    }

    fn resolve_function_type(
        &mut self,
        parsed: &parsed::FunctionType,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let type_parameters = HashMap::new(); // TODO

        let type_ = self
            .cross_referencer
            .resolve_function_return_type_function_pointer(parsed, &type_parameters)?;

        if let Type::FunctionPointer {
            argument_types,
            return_types,
        } = type_
        {
            return Ok(FunctionBodyItem::FunctionType(FunctionType {
                position: parsed.position.clone(),
                argument_types,
                return_types,
            }));
        }

        unreachable!()
    }

    fn resolve_call_by_name(
        &mut self,
        parsed: &parsed::CallByName,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        Ok(FunctionBodyItem::CallByName(CallByName {
            position: parsed.position.clone(),
        }))
    }

    fn resolve_integer(
        parsed_integer: &parsed::Integer,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let integer = Integer {
            position: parsed_integer.position.clone(),
            value: parsed_integer.value,
        };

        Ok(FunctionBodyItem::Integer(integer))
    }

    fn resolve_match(
        &mut self,
        parsed: &parsed::Match,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let case_blocks = parsed
            .case_blocks
            .iter()
            .map(|case_block| self.resolve_case_block(case_block))
            .collect::<Result<Vec<_>, _>>()?;

        let default_blocks = parsed
            .default_blocks
            .iter()
            .map(|default_block| self.resolve_default_block(default_block))
            .collect::<Result<Vec<_>, _>>()?;

        let match_ = Match {
            case_blocks,
            default_blocks,
            position: parsed.position.clone(),
        };

        Ok(FunctionBodyItem::Match(match_))
    }

    fn resolve_default_block(
        &mut self,
        parsed: &parsed::DefaultBlock,
    ) -> Result<DefaultBlock, CrossReferencerError> {
        let default_block = DefaultBlock {
            body: self.resolve_function_body(&parsed.body)?,
            position: parsed.position.clone(),
        };

        Ok(default_block)
    }

    fn resolve_case_block(
        &mut self,
        parsed: &parsed::CaseBlock,
    ) -> Result<CaseBlock, CrossReferencerError> {
        let variables: Vec<_> = parsed
            .label
            .variables
            .iter()
            .cloned()
            .map(|var| Variable::from(var))
            .collect();

        for variable in &variables {
            self.local_variables.insert(variable.value.clone());
        }

        let body_result = self.resolve_function_body(&parsed.body);

        for variable in &variables {
            self.local_variables.remove(&variable.value);
        }

        let case_block = CaseBlock {
            body: body_result?,
            position: parsed.position.clone(),
            enum_name: parsed.label.enum_name.value.clone(),
            variant_name: parsed.label.enum_variant.value.clone(),
        };

        Ok(case_block)
    }

    fn resolve_return(
        &self,
        parsed: &parsed::Return,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let return_ = Return {
            position: parsed.position.clone(),
        };

        Ok(FunctionBodyItem::Return(return_))
    }

    fn resolve_get_field(
        &self,
        parsed: &parsed::GetField,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let get_field = GetField {
            position: parsed.position.clone(),
            field_name: parsed.field_name.value.clone(),
        };

        Ok(FunctionBodyItem::GetField(get_field))
    }

    fn resolve_set_field(
        &mut self,
        parsed: &parsed::SetField,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let set_field = SetField {
            position: parsed.position.clone(),
            field_name: parsed.field_name.value.clone(),
            body: self.resolve_function_body(&parsed.body)?,
        };

        Ok(FunctionBodyItem::SetField(set_field))
    }

    fn resolve_use(
        &mut self,
        parsed: &parsed::Use,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let variables: Vec<_> = parsed
            .variables
            .iter()
            .cloned()
            .map(|var| Variable::from(var))
            .collect();

        for variable in &variables {
            self.local_variables.insert(variable.value.clone());
        }

        let body_result = self.resolve_function_body(&parsed.body);

        for variable in &variables {
            self.local_variables.remove(&variable.value);
        }

        Ok(FunctionBodyItem::Use(Use {
            body: body_result?,
            position: parsed.position.clone(),
            variables,
        }))
    }

    fn resolve_while(
        &mut self,
        parsed: &parsed::While,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let while_ = While {
            position: parsed.position.clone(),
            condition: self.resolve_function_body(&parsed.condition)?,
            body: self.resolve_function_body(&parsed.body)?,
        };

        Ok(FunctionBodyItem::While(while_))
    }

    fn resolve_string(
        parsed: &parsed::ParsedString,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let string = ParsedString {
            position: parsed.position.clone(),
            value: parsed.value.clone(),
        };

        Ok(FunctionBodyItem::String(string))
    }
}

#[cfg(test)]
mod tests {
    use std::{collections::HashMap, env, fs::read_to_string, path::PathBuf};

    use rstest::rstest;

    use crate::{
        common::position::Position,
        cross_referencer::errors::CrossReferencerError,
        cross_referencer::errors::CrossReferencerError::*,
        parser::{parser::parse, types::SourceFile},
        runner::runner::RunnerError,
        tokenizer::tokenizer::tokenize_filtered,
    };

    use super::{cross_reference, Output};

    const CURRENT_DIR: &str = "/testfolder";

    fn parse_file(code: &str, path: &PathBuf) -> Result<SourceFile, RunnerError> {
        let tokens = tokenize_filtered(code, Some(path.clone()))?;
        let parsed = parse(tokens)?;

        Ok(parsed)
    }

    fn cross_reference_files(
        files: HashMap<&str, &str>,
    ) -> Result<Output, Vec<CrossReferencerError>> {
        let stdlib_path = env::var("AAA_STDLIB_PATH").unwrap();
        let builtins_path = PathBuf::from(stdlib_path).join("builtins.aaa");
        let builtins_code = read_to_string(&builtins_path).unwrap();
        let parsed_builtins = parse_file(&builtins_code, &builtins_path).unwrap();

        let mut parsed_files = HashMap::from([(builtins_path.clone(), parsed_builtins)]);

        let current_dir = PathBuf::from(CURRENT_DIR);

        for (suffix, code) in files {
            let filename = current_dir.clone().join(suffix);
            let parsed_file = match parse_file(code, &filename) {
                Ok(parsed_file) => parsed_file,
                Err(err) => {
                    panic!("Parsing failed {}", err);
                }
            };
            parsed_files.insert(filename.clone(), parsed_file);
        }

        let entrypoint = current_dir.clone().join("main.aaa");

        cross_reference(parsed_files, entrypoint, builtins_path, current_dir)
    }

    fn cross_reference_file(code: &str) -> Result<Output, Vec<CrossReferencerError>> {
        let files = HashMap::from([("main.aaa", code)]);
        cross_reference_files(files)
    }

    fn get_single_error(result: Result<Output, Vec<CrossReferencerError>>) -> CrossReferencerError {
        let errors = match result {
            Ok(_) => unreachable!(),
            Err(errors) => errors,
        };
        assert_eq!(errors.len(), 1);
        errors.into_iter().next().unwrap()
    }

    #[test]
    fn test_no_error() {
        cross_reference_file("fn main { nop }").unwrap();
    }

    #[rstest]
    #[case("builtin fn foo", "function foo")]
    #[case("builtin struct bar", "struct bar")]
    fn test_unexpected_builtin(#[case] code: &str, #[case] expected_describe: &str) {
        let result = cross_reference_file(code);

        let UnexpectedBuiltin(error) = get_single_error(result) else {
            unreachable!()
        };

        assert_eq!(
            error.position,
            Position::new(PathBuf::from(CURRENT_DIR).join("main.aaa"), 1, 1)
        );

        assert_eq!(
            error.identifiable.describe(),
            String::from(expected_describe)
        );
    }

    #[rstest]
    fn test_colliding_identifiables() {
        let result = cross_reference_file("fn foo { nop }\nstruct foo {}");

        let CollidingIdentifiables(colliding) = get_single_error(result) else {
            unreachable!()
        };

        assert_eq!(colliding.first().describe(), "function foo".to_string());
        assert_eq!(colliding.second().describe(), "struct foo".to_string());
    }

    #[rstest]
    fn test_cyclic_dependency() {
        let files = HashMap::from([
            ("main.aaa", "from \"foo\" import bar\nstruct baz {}"),
            ("foo.aaa", "from \"main\" import baz\nstruct bar {}"),
        ]);

        let result = cross_reference_files(files);

        let CyclicDependency(cyclic) = get_single_error(result) else {
            unreachable!()
        };

        assert_eq!(
            cyclic.dependencies,
            vec![
                PathBuf::from(CURRENT_DIR).join("main.aaa"),
                PathBuf::from(CURRENT_DIR).join("foo.aaa"),
                PathBuf::from(CURRENT_DIR).join("main.aaa"),
            ]
        )
    }

    #[rstest]
    fn test_import_not_found() {
        let files = HashMap::from([("main.aaa", "from \"foo\" import bar"), ("foo.aaa", "")]);

        let result = cross_reference_files(files);

        let ImportNotFound(import_not_found) = get_single_error(result) else {
            unreachable!()
        };

        // TODO make position be the imported item as with indirect import
        assert_eq!(
            import_not_found.position,
            Position::new(PathBuf::from(CURRENT_DIR).join("main.aaa"), 1, 1)
        )
    }

    #[rstest]
    fn test_indirect_import() {
        let files = HashMap::from([
            ("main.aaa", "from \"foo\" import bar"),
            ("foo.aaa", "from \"bar\" import bar"),
            ("bar.aaa", "struct bar {}"),
        ]);

        let result = cross_reference_files(files);

        let IndirectImport(indirect_import) = get_single_error(result) else {
            unreachable!()
        };

        assert_eq!(
            indirect_import.position,
            Position::new(PathBuf::from(CURRENT_DIR).join("main.aaa"), 1, 19)
        )
    }

    #[rstest]
    fn test_invalid_argument() {
        let code = "fn foo { nop }\nfn bar args x as foo { nop }";

        let result = cross_reference_file(code);

        let InvalidArgument(invalid_argument) = get_single_error(result) else {
            unreachable!()
        };

        assert_eq!(
            invalid_argument.position,
            Position::new(PathBuf::from(CURRENT_DIR).join("main.aaa"), 2, 13)
        );

        assert_eq!(
            invalid_argument.identifiable.describe(),
            "function foo".to_string()
        );
    }

    #[rstest]
    fn test_invalid_return_type() {
        let code = "fn foo { nop }\nfn bar return foo { nop }";

        let result = cross_reference_file(code);

        let InvalidReturnType(invalid_return_type) = get_single_error(result) else {
            unreachable!()
        };

        assert_eq!(
            invalid_return_type.position,
            Position::new(PathBuf::from(CURRENT_DIR).join("main.aaa"), 2, 15)
        );

        assert_eq!(
            invalid_return_type.identifiable.describe(),
            "function foo".to_string()
        );
    }

    #[rstest]
    fn test_unknown_identifiable() {
        let code = "fn foo { bar }";

        let result = cross_reference_file(code);

        let UnknownIdentifiable(unknown_identifiable) = get_single_error(result) else {
            unreachable!()
        };

        assert_eq!(
            unknown_identifiable.position,
            Position::new(PathBuf::from(CURRENT_DIR).join("main.aaa"), 1, 10)
        );

        assert_eq!(unknown_identifiable.name, "bar".to_string());
    }
}

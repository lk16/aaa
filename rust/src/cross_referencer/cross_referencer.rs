use std::{
    cell::{Cell, RefCell},
    collections::{hash_map::Entry as HashMapEntry, HashMap, HashSet},
    fmt::Debug,
    path::PathBuf,
    rc::Rc,
};

use super::{
    errors::{
        cyclic_dependency, get_function_not_found, import_not_found, indirect_import,
        name_collision, unexpected_builtin, unknown_identifiable, CrossReferencerError,
    },
    types::{
        function_body::{
            Assignment, Boolean, Branch, Call, CallArgument, CallEnum, CallEnumConstructor,
            CallFunction, CallLocalVariable, CallStruct, CaseBlock, Char, DefaultBlock, Foreach,
            FunctionBody, FunctionBodyItem, GetField, GetFunction, Integer, Match, ParsedString,
            Return, SetField, Use, Variable, While,
        },
        identifiable::{
            Argument, Enum, EnumType, Function, FunctionPointerType, FunctionSignature,
            Identifiable, Import, ResolvedEnum, ResolvedStruct, ReturnTypes, Struct, StructType,
            Type,
        },
    },
};
use crate::{
    common::{position::Position, traits::HasPosition},
    cross_referencer::{errors::get_function_non_function, types::function_body::FunctionType},
    parser::types::{self as parsed, SourceFile},
    type_checker::errors::NameCollision,
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

#[derive(Clone)]
pub struct Output {
    pub identifiables: HashMap<(PathBuf, String), Identifiable>,
    pub builtins_path: PathBuf,
    pub entrypoint_path: PathBuf,
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
            builtins_path: self.builtins_path,
            entrypoint_path: self.entrypoint_path,
        })
    }

    fn cross_reference_file_with_dependencies(
        &mut self,
        path: &PathBuf,
    ) -> Result<(), CrossReferencerError> {
        if self.dependency_stack.contains(&path) {
            let mut dependencies = self.dependency_stack.clone();
            dependencies.push(path.clone());

            return cyclic_dependency(dependencies);
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
                let error = unexpected_builtin(identifiable.position(), identifiable.clone());
                self.errors.push(error);
            }
        }

        for identifiable in indentifiables.iter() {
            let key = identifiable.key();

            match self.identifiables.entry(key) {
                HashMapEntry::Vacant(entry) => {
                    entry.insert(identifiable.clone());
                }
                HashMapEntry::Occupied(entry) => {
                    let error = CrossReferencerError::NameCollision(NameCollision {
                        items: [
                            Box::new(entry.get().clone()),
                            Box::new(identifiable.clone()),
                        ],
                    });

                    self.errors.push(error);
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
            if let Err(error) = self.resolve_import(import) {
                self.errors.push(error);
            }
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

    fn resolve_import(&self, import_rc: Rc<RefCell<Import>>) -> Result<(), CrossReferencerError> {
        let mut import = import_rc.borrow_mut();
        let target_key = import.target_key();

        let target = match self.identifiables.get(&target_key) {
            Some(identifiable) => identifiable,
            None => {
                return import_not_found(import.position(), import.name(), import.target_key().0)
            }
        };

        if let Identifiable::Import(_) = target {
            return indirect_import(import.parsed_item.position.clone());
        }

        import.resolved = Some(target.clone());

        Ok(())
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
            let name = &parsed_parameter.value;
            let key = (struct_.position().path, name.clone());

            if let Some(identifiable) = self.identifiables.get(&key) {
                let error = CrossReferencerError::NameCollision(NameCollision {
                    items: [
                        Box::new(Identifiable::Struct(struct_rc.clone())),
                        Box::new(identifiable.clone()),
                    ],
                });

                return Err(error);
            }

            let parameter = parsed_parameter.clone().into();
            let type_ = Type::Parameter(parameter);
            resolved_parameters.insert(name.clone(), type_);
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

        let type_ = Type::FunctionPointer(FunctionPointerType {
            argument_types,
            return_types,
        });

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
            Identifiable::Enum(enum_) => Type::Enum(EnumType { enum_, parameters }),
            Identifiable::Struct(struct_) => Type::Struct(StructType {
                struct_,
                parameters,
            }),
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
            Identifiable::Enum(enum_) => Type::Enum(EnumType { enum_, parameters }),
            Identifiable::Struct(struct_) => Type::Struct(StructType {
                struct_,
                parameters,
            }),
            _ => unreachable!(),
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
                None => return unknown_identifiable(position, name),
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

        unknown_identifiable(position, name)
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
            let name = &parsed_parameter.value;
            let key = (enum_.position().path, name.clone());

            if let Some(identifier) = self.identifiables.get(&key) {
                let error = CrossReferencerError::NameCollision(NameCollision {
                    items: [
                        Box::new(Identifiable::Enum(enum_rc.clone())),
                        Box::new(identifier.clone()),
                    ],
                });

                return Err(error);
            }

            let parameter = parsed_parameter.clone().into();
            let type_ = Type::Parameter(parameter);
            resolved_parameters.insert(name.clone(), type_);
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
            let name = &parsed_parameter.value;
            let key = (function.position().path, name.clone());

            if let Some(identifier) = self.identifiables.get(&key) {
                let error = CrossReferencerError::NameCollision(NameCollision {
                    items: [
                        Box::new(Identifiable::Function(function_rc.clone())),
                        Box::new(identifier.clone()),
                    ],
                });

                return Err(error);
            }

            let parameter = parsed_parameter.clone().into();
            let type_ = Type::Parameter(parameter);
            resolved_parameters.insert(name.clone(), type_);
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
        let type_ = self.resolve_function_return_type(&parsed.type_, type_parameters)?;

        if let Ok(identifier) = self.get_identifiable(parsed.position(), parsed.name.value.clone())
        {
            return name_collision(Box::new(parsed.clone()), Box::new(identifier));
        }

        let name = parsed.name.value.clone();
        let position = parsed.position.clone();
        Ok(Argument::new(position, type_, name))
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

        return Ok(Type::FunctionPointer(FunctionPointerType {
            argument_types,
            return_types,
        }));
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
            Identifiable::Enum(enum_) => Type::Enum(EnumType { enum_, parameters }),
            Identifiable::Struct(struct_) => Type::Struct(StructType {
                struct_,
                parameters,
            }),
            _ => unreachable!(),
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
                    Identifiable::Struct(struct_) => Type::Struct(StructType {
                        struct_,
                        parameters,
                    }),
                    Identifiable::Enum(enum_) => Type::Enum(EnumType { enum_, parameters }),
                    _ => todo!(), // InvalidType
                }
            }
            Some(_type_) => Type::Parameter(regular_parsed_type_parameter.clone().into()),
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
            ParsedItem::GetFunction(get_function) => self.resolve_get_function(get_function),
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

        let identifiable = self
            .cross_referencer
            .get_identifiable(position.clone(), name)?;

        let type_parameters = self.function.signature().type_parameters.clone();

        let parameters: Vec<_> = parsed
            .parameters()
            .iter()
            .cloned()
            .map(|param| {
                self.cross_referencer
                    .resolve_type_parameter(&param, &type_parameters)
            })
            .collect::<Result<Vec<_>, _>>()?;

        match identifiable {
            Identifiable::Import(_) => unreachable!(),
            Identifiable::Function(function_rc) => {
                return Ok(FunctionBodyItem::CallFunction(CallFunction {
                    function: function_rc.clone(),
                    type_parameters: parameters,
                    position: parsed.position(),
                }))
            }
            Identifiable::Enum(enum_rc) => {
                return Ok(FunctionBodyItem::CallEnum(CallEnum {
                    enum_: enum_rc.clone(),
                    type_parameters: parameters,
                    position: parsed.position(),
                }))
            }
            Identifiable::Struct(struct_rc) => {
                return Ok(FunctionBodyItem::CallStruct(CallStruct {
                    struct_: struct_rc.clone(),
                    type_parameters: parameters,
                    position: parsed.position(),
                }))
            }
            Identifiable::EnumConstructor(enum_ctor) => {
                return Ok(FunctionBodyItem::CallEnumConstructor(CallEnumConstructor {
                    enum_constructor: enum_ctor.clone(),
                    type_parameters: parameters,
                    position: parsed.position(),
                }));
            }
        }
    }

    fn resolve_function_type(
        &mut self,
        parsed: &parsed::FunctionType,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        // TODO #154 Support using type parameters in function pointer values
        let type_parameters = HashMap::new();

        let type_ = self
            .cross_referencer
            .resolve_function_return_type_function_pointer(parsed, &type_parameters)?;

        let Type::FunctionPointer(function_pointer_type) = type_ else {
            unreachable!()
        };

        Ok(FunctionBodyItem::FunctionType(FunctionType {
            position: parsed.position.clone(),
            argument_types: function_pointer_type.argument_types,
            return_types: function_pointer_type.return_types,
        }))
    }

    fn resolve_get_function(
        &mut self,
        parsed: &parsed::GetFunction,
    ) -> Result<FunctionBodyItem, CrossReferencerError> {
        let position = parsed.position.clone();
        let name = parsed.target.value.clone();

        let identifiable = match self
            .cross_referencer
            .get_identifiable(position.clone(), name.clone())
        {
            Err(_) => return get_function_not_found(position, name),
            Ok(identifiable) => identifiable,
        };

        let Identifiable::Function(target) = identifiable else {
            return get_function_non_function(position, name, identifiable);
        };

        Ok(FunctionBodyItem::GetFunction(GetFunction {
            position: parsed.position.clone(),
            function_name: parsed.target.value.clone(),
            target,
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
            self.local_variables.insert(variable.name.clone());
        }

        let body_result = self.resolve_function_body(&parsed.body);

        for variable in &variables {
            self.local_variables.remove(&variable.name);
        }

        let case_block = CaseBlock {
            body: body_result?,
            position: parsed.position.clone(),
            enum_name: parsed.label.enum_name.value.clone(),
            variant_name: parsed.label.enum_variant.value.clone(),
            variables,
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
            target: Cell::new(None), // Target is set in type checker
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
            target: Cell::new(None), // Target is set in type checker
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
            self.local_variables.insert(variable.name.clone());
        }

        let body_result = self.resolve_function_body(&parsed.body);

        for variable in &variables {
            self.local_variables.remove(&variable.name);
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

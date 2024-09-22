use std::{cell::RefCell, collections::HashMap, fmt::Display, iter::zip, path::PathBuf, rc::Rc};

use crate::{
    common::{formatting::join_display, position::Position, traits::HasPosition},
    parser::types::{self as parsed, RegularType},
};

use super::function_body::FunctionBody;

pub struct Struct {
    pub is_builtin: bool,
    pub parsed: parsed::Struct,
    pub resolved: Option<ResolvedStruct>,
}

impl PartialEq for Struct {
    fn eq(&self, other: &Self) -> bool {
        self.name() == other.name() && self.position() == other.position()
    }
}

impl From<parsed::Struct> for Struct {
    fn from(parsed: parsed::Struct) -> Self {
        Self {
            is_builtin: parsed.fields.is_none(),
            parsed,
            resolved: None,
        }
    }
}

impl HasPosition for Struct {
    fn position(&self) -> Position {
        self.parsed.position.clone()
    }
}

impl Struct {
    pub fn key(&self) -> (PathBuf, String) {
        (self.position().path, self.name())
    }

    pub fn name(&self) -> String {
        self.parsed.name.value.clone()
    }

    pub fn resolved(&self) -> &ResolvedStruct {
        let Some(resolved) = &self.resolved else {
            unreachable!()
        };

        resolved
    }

    pub fn expected_parameter_count(&self) -> usize {
        self.resolved().type_parameters.len()
    }

    pub fn fields(&self) -> &HashMap<String, Type> {
        &self.resolved().fields
    }

    pub fn field(&self, name: &String) -> Option<&Type> {
        self.fields().get(name)
    }

    pub fn parameter_names(&self) -> Vec<String> {
        // We use parsed, because it maintains order of the parameters.
        // This is not the case in resolved, which stores parameters in a HashMap, losing the order.
        self.parsed
            .parameters
            .iter()
            .cloned()
            .map(|param| param.value)
            .collect()
    }

    pub fn parameter_mapping(&self, parameter_vec: &Vec<Type>) -> HashMap<String, Type> {
        let mut mapping = HashMap::new();

        for (key, value) in zip(self.parameter_names(), parameter_vec) {
            mapping.insert(key.clone(), value.clone());
        }

        mapping
    }
}

pub struct ResolvedStruct {
    pub type_parameters: HashMap<String, Type>,
    pub fields: HashMap<String, Type>,
}

#[derive(Clone, PartialEq)]
pub struct TypeParameter {
    pub position: Position,
    pub name: String,
}

impl Display for TypeParameter {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.name)
    }
}

impl From<parsed::Identifier> for TypeParameter {
    fn from(identifier: parsed::Identifier) -> Self {
        TypeParameter {
            position: identifier.position,
            name: identifier.value,
        }
    }
}

impl From<RegularType> for TypeParameter {
    fn from(regular_type: RegularType) -> Self {
        TypeParameter {
            position: regular_type.position,
            name: regular_type.name.value,
        }
    }
}

impl HasPosition for TypeParameter {
    fn position(&self) -> Position {
        self.position.clone()
    }
}

#[derive(Clone, PartialEq)]
pub enum Type {
    FunctionPointer(FunctionPointerType),
    Struct(StructType),
    Enum(EnumType),
    Parameter(TypeParameter),
}

impl Display for Type {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::FunctionPointer(function_pointer) => write!(f, "{}", function_pointer),
            Self::Struct(struct_) => write!(f, "{}", struct_),
            Self::Enum(enum_) => write!(f, "{}", enum_),
            Self::Parameter(param) => write!(f, "{}", param),
        }
    }
}

impl Type {
    pub fn kind(&self) -> &'static str {
        match &self {
            &Self::FunctionPointer(_) => "function pointer",
            &Self::Struct(_) => "struct",
            &Self::Enum(_) => "enum",
            &Self::Parameter(_) => "parameter",
        }
    }
}

impl HasPosition for Type {
    fn position(&self) -> Position {
        match &self {
            Self::FunctionPointer(_) => todo!(),
            &Self::Struct(struct_type) => struct_type.struct_.borrow().position(),
            &Self::Enum(enum_type) => enum_type.enum_.borrow().position(),
            &Self::Parameter(parameter) => parameter.position.clone(),
        }
    }
}

#[derive(Clone, PartialEq)]
pub struct EnumType {
    pub enum_: Rc<RefCell<Enum>>,
    pub parameters: Vec<Type>,
}

impl Display for EnumType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let enum_ = self.enum_.borrow();
        write!(f, "{}", enum_.name())?;

        if !self.parameters.is_empty() {
            let joined_parameters = join_display(", ", &self.parameters);
            write!(f, "[{}]", joined_parameters)?;
        }

        Ok(())
    }
}

#[derive(Clone, PartialEq)]
pub struct StructType {
    pub struct_: Rc<RefCell<Struct>>,
    pub parameters: Vec<Type>,
}

impl Display for StructType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let struct_ = self.struct_.borrow();
        write!(f, "{}", struct_.name())?;

        if !self.parameters.is_empty() {
            let joined_parameters = join_display(", ", &self.parameters);
            write!(f, "[{}]", joined_parameters)?;
        }

        Ok(())
    }
}

#[derive(Clone, PartialEq)]
pub struct FunctionPointerType {
    pub argument_types: Vec<Type>,
    pub return_types: ReturnTypes,
}

impl Display for FunctionPointerType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let joined_args = join_display(", ", &self.argument_types);

        write!(f, "fn[{}][{}]", joined_args, self.return_types)?;

        Ok(())
    }
}

#[derive(Clone, PartialEq)]
pub enum ReturnTypes {
    Sometimes(Vec<Type>),
    Never,
}

impl Display for ReturnTypes {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Never => return write!(f, "never"),
            Self::Sometimes(types) => {
                let joined_types = join_display(", ", types);
                write!(f, "{}", joined_types)
            }
        }
    }
}

#[derive(Clone)]
pub struct Argument {
    pub position: Position,
    pub type_: Type,
    pub name: String,
}

impl Argument {
    pub fn new(position: Position, type_: Type, name: String) -> Self {
        Self {
            position,
            type_,
            name,
        }
    }
}

impl HasPosition for Argument {
    fn position(&self) -> Position {
        self.position.clone()
    }
}

impl Display for Argument {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "argument {}", self.name)
    }
}

pub struct Enum {
    pub parsed: parsed::Enum,
    pub resolved: Option<ResolvedEnum>,
    pub is_builtin: bool,
}

impl PartialEq for Enum {
    fn eq(&self, other: &Self) -> bool {
        self.name() == other.name() && self.position() == other.position()
    }
}

impl From<parsed::Enum> for Enum {
    fn from(parsed: parsed::Enum) -> Self {
        Self {
            is_builtin: false, // TODO #224 add is_builtin to parsed Enum, Struct and Function
            parsed,
            resolved: None,
        }
    }
}

impl Enum {
    pub fn key(&self) -> (PathBuf, String) {
        (self.position().path, self.name())
    }

    pub fn name(&self) -> String {
        self.parsed.name.value.clone()
    }

    pub fn resolved(&self) -> &ResolvedEnum {
        let Some(resolved) = &self.resolved else {
            unreachable!()
        };

        resolved
    }

    pub fn expected_parameter_count(&self) -> usize {
        self.resolved().type_parameters.len()
    }

    pub fn variants(&self) -> &HashMap<String, Vec<Type>> {
        &self.resolved().variants
    }

    pub fn zero_variant_name(&self) -> &String {
        &self.parsed.variants.get(0).unwrap().name.value
    }

    pub fn zero_variant_data(&self) -> &Vec<Type> {
        let name = self.zero_variant_name();
        &self.variants().get(name).unwrap()
    }

    pub fn parameter_names(&self) -> Vec<String> {
        // We use parsed, because it maintains order of the parameters.
        // This is not the case in resolved, which stores parameters in a HashMap, losing the order.
        self.parsed
            .parameters
            .iter()
            .cloned()
            .map(|param| param.value)
            .collect()
    }

    pub fn parameter_mapping(&self, parameter_vec: &Vec<Type>) -> HashMap<String, Type> {
        let mut mapping = HashMap::new();

        for (key, value) in zip(self.parameter_names(), parameter_vec) {
            mapping.insert(key.clone(), value.clone());
        }

        mapping
    }
}

impl HasPosition for Enum {
    fn position(&self) -> Position {
        self.parsed.position.clone()
    }
}

pub struct ResolvedEnum {
    pub type_parameters: HashMap<String, Type>,
    pub variants: HashMap<String, Vec<Type>>,
}

pub struct EnumConstructor {
    pub enum_: Rc<RefCell<Enum>>,
    pub parsed: parsed::EnumVariant,
}

impl From<(Rc<RefCell<Enum>>, parsed::EnumVariant)> for EnumConstructor {
    fn from(tuple: (Rc<RefCell<Enum>>, parsed::EnumVariant)) -> Self {
        let (enum_, parsed) = tuple;
        Self { enum_, parsed }
    }
}

impl EnumConstructor {
    pub fn name(&self) -> String {
        format!("{}:{}", self.enum_.borrow().name(), self.variant_name())
    }

    pub fn variant_name(&self) -> String {
        self.parsed.name.value.clone()
    }

    pub fn data(&self) -> Vec<Type> {
        let enum_ = self.enum_.borrow();

        let variants = match &enum_.resolved {
            Some(resolved) => &resolved.variants,
            None => unreachable!(),
        };

        variants.get(&self.variant_name()).unwrap().clone()
    }
}

impl HasPosition for EnumConstructor {
    fn position(&self) -> Position {
        self.parsed.position.clone()
    }
}

pub struct FunctionSignature {
    pub type_parameters: HashMap<String, Type>,
    pub arguments: Vec<Argument>,
    pub return_types: ReturnTypes,
}

impl FunctionSignature {
    pub fn argument_types(&self) -> Vec<Type> {
        self.arguments.iter().map(|arg| arg.type_.clone()).collect()
    }
}

pub struct Function {
    pub parsed: parsed::Function,
    pub resolved_signature: Option<FunctionSignature>,
    pub resolved_body: Option<FunctionBody>,
    pub is_builtin: bool,
}

impl From<parsed::Function> for Function {
    fn from(parsed: parsed::Function) -> Self {
        Self {
            is_builtin: parsed.body.is_none(),
            parsed: parsed,
            resolved_signature: None,
            resolved_body: None,
        }
    }
}

impl Function {
    pub fn name(&self) -> String {
        self.parsed.name()
    }

    pub fn get_argument(&self, name: &String) -> Option<&Argument> {
        self.signature()
            .arguments
            .iter()
            .filter(|arg| &arg.name == name)
            .next()
    }

    pub fn has_argument(&self, name: &String) -> bool {
        self.get_argument(name).is_some()
    }

    pub fn signature(&self) -> &FunctionSignature {
        match &self.resolved_signature {
            None => unreachable!(),
            Some(signature) => signature,
        }
    }

    pub fn body(&self) -> &FunctionBody {
        match &self.resolved_body {
            None => unreachable!(),
            Some(body) => body,
        }
    }

    pub fn arguments(&self) -> &Vec<Argument> {
        &self.signature().arguments
    }

    pub fn return_types(&self) -> &ReturnTypes {
        &self.signature().return_types
    }

    pub fn type_name(&self) -> Option<String> {
        self.parsed.name.type_name()
    }
}

impl HasPosition for Function {
    fn position(&self) -> Position {
        self.parsed.position.clone()
    }
}

pub struct Import {
    pub parsed_import: parsed::Import,
    pub parsed_item: parsed::ImportItem,
    pub resolved: Option<Identifiable>,
}

impl From<(parsed::Import, parsed::ImportItem)> for Import {
    fn from(tuple: (parsed::Import, parsed::ImportItem)) -> Self {
        let (parsed_import, parsed_item) = tuple;
        Self {
            parsed_import,
            parsed_item,
            resolved: None,
        }
    }
}

impl Import {
    pub fn name(&self) -> String {
        match &self.parsed_item.alias {
            Some(alias) => alias.value.clone(),
            None => self.parsed_item.name.value.clone(),
        }
    }

    pub fn target_key(&self) -> (PathBuf, String) {
        let current_dir = std::env::current_dir().unwrap();
        (
            self.parsed_import.get_source_path(&current_dir),
            self.parsed_item.name.value.clone(),
        )
    }
}

impl HasPosition for Import {
    fn position(&self) -> Position {
        self.parsed_import.position.clone()
    }
}

#[derive(Clone)]
pub enum Identifiable {
    Struct(Rc<RefCell<Struct>>),
    Enum(Rc<RefCell<Enum>>),
    EnumConstructor(Rc<RefCell<EnumConstructor>>),
    Function(Rc<RefCell<Function>>),
    Import(Rc<RefCell<Import>>),
}

impl From<parsed::Struct> for Identifiable {
    fn from(parsed: parsed::Struct) -> Self {
        Identifiable::Struct(Rc::new(RefCell::new(parsed.into())))
    }
}

impl From<parsed::Enum> for Identifiable {
    fn from(parsed: parsed::Enum) -> Self {
        Identifiable::Enum(Rc::new(RefCell::new(parsed.into())))
    }
}

impl From<parsed::Function> for Identifiable {
    fn from(parsed: parsed::Function) -> Self {
        Identifiable::Function(Rc::new(RefCell::new(parsed.into())))
    }
}

impl From<(Rc<RefCell<Enum>>, parsed::EnumVariant)> for Identifiable {
    fn from(tuple: (Rc<RefCell<Enum>>, parsed::EnumVariant)) -> Self {
        Identifiable::EnumConstructor(Rc::new(RefCell::new(tuple.into())))
    }
}

impl From<(parsed::Import, parsed::ImportItem)> for Identifiable {
    fn from(tuple: (parsed::Import, parsed::ImportItem)) -> Self {
        Identifiable::Import(Rc::new(RefCell::new(tuple.into())))
    }
}

impl Identifiable {
    pub fn is_builtin(&self) -> bool {
        match self {
            Identifiable::Function(function) => function.borrow().is_builtin,
            Identifiable::Struct(struct_) => struct_.borrow().is_builtin,
            Identifiable::Enum(enum_) => enum_.borrow().is_builtin,
            Identifiable::EnumConstructor(enum_ctor) => {
                enum_ctor.borrow().enum_.borrow().is_builtin
            }
            _ => false,
        }
    }

    pub fn name(&self) -> String {
        match self {
            Identifiable::Enum(enum_) => enum_.borrow().name(),
            Identifiable::EnumConstructor(enum_ctor) => enum_ctor.borrow().name(),
            Identifiable::Function(function) => function.borrow().name(),
            Identifiable::Import(import) => import.borrow().name(),
            Identifiable::Struct(struct_) => struct_.borrow().name(),
        }
    }

    pub fn key(&self) -> (PathBuf, String) {
        (self.position().path, self.name())
    }
}

impl HasPosition for Identifiable {
    fn position(&self) -> Position {
        match self {
            Identifiable::Enum(enum_) => enum_.borrow().position(),
            Identifiable::EnumConstructor(enum_ctor) => enum_ctor.borrow().position(),
            Identifiable::Function(function) => function.borrow().position(),
            Identifiable::Import(import) => import.borrow().position(),
            Identifiable::Struct(struct_) => struct_.borrow().position(),
        }
    }
}

impl Display for Identifiable {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let prefix = match self {
            Identifiable::Enum(_) => "enum ",
            Identifiable::EnumConstructor(_) => "enum constructor",
            Identifiable::Function(_) => "function",
            Identifiable::Import(_) => "import",
            Identifiable::Struct(_) => "struct",
        };

        write!(f, "{} {}", prefix, self.name())
    }
}

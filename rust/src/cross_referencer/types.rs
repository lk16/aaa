#![allow(dead_code)] // TODO

use std::{cell::RefCell, collections::HashMap, path::PathBuf, rc::Rc};

use crate::{
    common::position::Position,
    parser::types::{self as parsed},
};

pub struct Struct {
    pub parsed: parsed::Struct,
    pub resolved: Option<ResolvedStruct>,
}

impl From<parsed::Struct> for Struct {
    fn from(parsed: parsed::Struct) -> Self {
        Self {
            parsed,
            resolved: None,
        }
    }
}

impl Struct {
    pub fn key(&self) -> (PathBuf, String) {
        (self.position().path, self.name())
    }

    pub fn name(&self) -> String {
        self.parsed.name.value.clone()
    }

    pub fn position(&self) -> Position {
        self.parsed.position.clone()
    }
}

pub struct ResolvedStruct {
    pub type_parameters: HashMap<String, Type>,
    pub fields: HashMap<String, Type>,
}

#[derive(Clone)]
pub struct TypeParameter {
    pub position: Position,
    pub name: String,
}

impl TypeParameter {
    pub fn from_parsed(identifier: &parsed::Identifier) -> Self {
        Self {
            name: identifier.value.clone(),
            position: identifier.position.clone(),
        }
    }
}

#[derive(Clone)]
pub enum Type {
    FunctionPointer {
        argument_types: Vec<Type>,
        return_types: ReturnTypes,
    },
    Struct {
        struct_: Rc<RefCell<Struct>>,
        parameters: Vec<Type>,
    },
    Enum {
        enum_: Rc<RefCell<Enum>>,
        parameters: Vec<Type>,
    },
    Parameter(TypeParameter),
}

#[derive(Clone)]
pub enum ReturnTypes {
    Sometimes(Vec<Type>),
    Never,
}

pub struct Argument {
    pub type_: Type,
    pub name: String,
}

pub struct Enum {
    pub parsed: parsed::Enum,
    pub resolved: Option<ResolvedEnum>,
}

impl From<parsed::Enum> for Enum {
    fn from(parsed: parsed::Enum) -> Self {
        Self {
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

    pub fn position(&self) -> Position {
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
    pub fn key(&self) -> (PathBuf, String) {
        (self.position().path, self.name())
    }

    pub fn name(&self) -> String {
        format!("{}:{}", self.enum_.borrow().name(), self.variant_name())
    }

    pub fn variant_name(&self) -> String {
        self.parsed.name.value.clone()
    }

    pub fn position(&self) -> Position {
        self.parsed.position.clone()
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

pub struct FunctionSignature {
    pub type_parameters: HashMap<String, Type>,
    pub arguments: Vec<Argument>,
    pub return_types: ReturnTypes,
}

pub struct Function {
    pub parsed: parsed::Function,
    pub resolved_signature: Option<FunctionSignature>,
    pub resolved_body: Option<FunctionBody>,
}

impl From<parsed::Function> for Function {
    fn from(parsed: parsed::Function) -> Self {
        Self {
            parsed: parsed,
            resolved_signature: None,
            resolved_body: None,
        }
    }
}

impl Function {
    pub fn key(&self) -> (PathBuf, String) {
        (self.position().path, self.name())
    }

    pub fn name(&self) -> String {
        self.parsed.name()
    }

    pub fn position(&self) -> Position {
        self.parsed.position.clone()
    }

    pub fn has_argument(&self, name: &String) -> bool {
        self.parsed
            .arguments
            .iter()
            .any(|arg| &arg.name.value == name)
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

    pub fn position(&self) -> Position {
        self.parsed_import.position.clone()
    }

    pub fn key(&self) -> (PathBuf, String) {
        (self.position().path, self.name())
    }

    pub fn target_key(&self) -> (PathBuf, String) {
        let current_dir = std::env::current_dir().unwrap();
        (
            self.parsed_import.get_source_path(&current_dir),
            self.parsed_item.name.value.clone(),
        )
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
    pub fn get_enum_rc(&self) -> Rc<RefCell<Enum>> {
        match self {
            Self::Enum(enum_) => enum_.clone(),
            _ => unreachable!(),
        }
    }

    pub fn is_builtin(&self) -> bool {
        // TODO this is hacky, add a boolean field instead.
        match self {
            Identifiable::Function(function) => {
                let function = function.borrow();
                function.parsed.body.is_none()
            }
            Identifiable::Struct(struct_) => {
                let struct_ = struct_.borrow();
                struct_.parsed.fields.is_none()
            }
            _ => false,
        }
    }

    pub fn position(&self) -> Position {
        match self {
            Identifiable::Enum(enum_) => enum_.borrow().position(),
            Identifiable::EnumConstructor(enum_ctor) => enum_ctor.borrow().position(),
            Identifiable::Function(function) => function.borrow().position(),
            Identifiable::Import(import) => import.borrow().position(),
            Identifiable::Struct(struct_) => struct_.borrow().position(),
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

    pub fn describe(&self) -> String {
        let prefix = match self {
            Identifiable::Enum(_) => "enum ",
            Identifiable::EnumConstructor(_) => "enum constructor",
            Identifiable::Function(_) => "function",
            Identifiable::Import(_) => "import",
            Identifiable::Struct(_) => "struct",
        };

        format!("{} {}", prefix, self.name())
    }
}

pub struct FunctionBody {
    pub position: Position,
    pub items: Vec<FunctionBodyItem>,
}

pub enum FunctionBodyItem {
    Assignment(Assignment),
    Branch(Branch),
    Boolean(Boolean),
    Call(Call),
    CallArgument(CallArgument),
    CallFunction(CallFunction),
    CallEnum(CallEnum),
    CallEnumConstructor(CallEnumConstructor),
    CallLocalVariable(CallLocalVariable),
    CallStruct(CallStruct),
    Char(Char),
    Foreach(Foreach),
    FunctionType(FunctionType),
    CallByName(CallByName),
    Integer(Integer),
    Match(Match),
    Return(Return),
    GetField(GetField),
    SetField(SetField),
    Use(Use),
    While(While),
    String(ParsedString),
}

pub struct Variable {
    pub position: Position,
    pub value: String,
}

impl From<parsed::Identifier> for Variable {
    fn from(identifier: parsed::Identifier) -> Self {
        Variable {
            position: identifier.position,
            value: identifier.value,
        }
    }
}

pub struct Assignment {
    pub position: Position,
    pub variables: Vec<Variable>,
    pub body: FunctionBody,
}

pub struct Branch {
    pub position: Position,
    pub condition: FunctionBody,
    pub if_body: FunctionBody,
    pub else_body: Option<FunctionBody>,
}

pub struct Boolean {
    pub position: Position,
    pub value: bool,
}

pub struct Call {
    pub position: Position,
}

pub struct Char {
    pub position: Position,
    pub value: char,
}

pub struct Foreach {
    pub position: Position,
    pub body: FunctionBody,
}

pub struct CallArgument {
    pub position: Position,
    pub name: String,
}

pub struct CallEnum {
    pub position: Position,
    pub function: Rc<RefCell<Enum>>,
    pub type_parameters: HashMap<String, Type>,
}

pub struct CallEnumConstructor {
    pub position: Position,
    pub enum_constructor: Rc<RefCell<EnumConstructor>>,
    pub type_parameters: HashMap<String, Type>,
}

pub struct CallFunction {
    pub position: Position,
    pub function: Rc<RefCell<Function>>,
    pub type_parameters: HashMap<String, Type>,
}

pub struct CallLocalVariable {
    pub position: Position,
    pub name: String,
}

pub struct CallStruct {
    pub position: Position,
    pub function: Rc<RefCell<Struct>>,
    pub type_parameters: HashMap<String, Type>,
}

pub struct FunctionType {
    pub position: Position,
    pub argument_types: Vec<Type>,
    pub return_types: ReturnTypes,
}

pub struct CallByName {
    pub position: Position,
}

pub struct Integer {
    pub position: Position,
    pub value: isize,
}

pub struct Match {
    pub position: Position,
    pub case_blocks: Vec<CaseBlock>,
    pub default_blocks: Vec<DefaultBlock>,
}

pub struct CaseBlock {
    pub position: Position,
    pub enum_name: String,
    pub variant_name: String,
    pub body: FunctionBody,
}

pub struct DefaultBlock {
    pub position: Position,
    pub body: FunctionBody,
}

pub struct Return {
    pub position: Position,
}

pub struct GetField {
    pub position: Position,
    pub field_name: String,
}

pub struct SetField {
    pub position: Position,
    pub field_name: String,
    pub body: FunctionBody,
}

pub struct Use {
    pub position: Position,
    pub body: FunctionBody,
    pub variables: Vec<Variable>,
}

pub struct While {
    pub position: Position,
    pub condition: FunctionBody,
    pub body: FunctionBody,
}

pub struct ParsedString {
    // TODO consider renaming
    pub position: Position,
    pub value: String,
}

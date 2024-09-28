use std::cell::Cell;
use std::rc::Rc;
use std::{cell::RefCell, fmt::Display};

use crate::common::position::Position;
use crate::parser::types as parsed;

use super::identifiable::{Enum, EnumConstructor, Function, ReturnTypes, Struct, Type};

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
    GetFunction(GetFunction),
    Integer(Integer),
    Match(Match),
    Return(Return),
    GetField(GetField),
    SetField(SetField),
    Use(Use),
    While(While),
    String(ParsedString),
}

impl Display for FunctionBodyItem {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Assignment(_) => write!(f, "Assignment"),
            Self::Branch(_) => write!(f, "Branch"),
            Self::Boolean(_) => write!(f, "Boolean"),
            Self::Call(_) => write!(f, "Call"),
            Self::CallArgument(_) => write!(f, "CallArgument"),
            Self::CallFunction(_) => write!(f, "CallFunction"),
            Self::CallEnum(_) => write!(f, "CallEnum"),
            Self::CallEnumConstructor(_) => write!(f, "CallEnumConstructor"),
            Self::CallLocalVariable(_) => write!(f, "CallLocalVariable"),
            Self::CallStruct(_) => write!(f, "CallStruct"),
            Self::Char(_) => write!(f, "Char"),
            Self::Foreach(_) => write!(f, "Foreach"),
            Self::FunctionType(_) => write!(f, "FunctionType"),
            Self::GetFunction(_) => write!(f, "CallByName"),
            Self::Integer(_) => write!(f, "Integer"),
            Self::Match(_) => write!(f, "Match"),
            Self::Return(_) => write!(f, "Return"),
            Self::GetField(_) => write!(f, "GetField"),
            Self::SetField(_) => write!(f, "SetField"),
            Self::Use(_) => write!(f, "Use"),
            Self::While(_) => write!(f, "While"),
            Self::String(_) => write!(f, "String"),
        }
    }
}

impl FunctionBodyItem {
    pub fn position(&self) -> Position {
        match self {
            Self::Assignment(item) => item.position.clone(),
            Self::Branch(item) => item.position.clone(),
            Self::Boolean(item) => item.position.clone(),
            Self::Call(item) => item.position.clone(),
            Self::CallArgument(item) => item.position.clone(),
            Self::CallFunction(item) => item.position.clone(),
            Self::CallEnum(item) => item.position.clone(),
            Self::CallEnumConstructor(item) => item.position.clone(),
            Self::CallLocalVariable(item) => item.position.clone(),
            Self::CallStruct(item) => item.position.clone(),
            Self::Char(item) => item.position.clone(),
            Self::Foreach(item) => item.position.clone(),
            Self::FunctionType(item) => item.position.clone(),
            Self::GetFunction(item) => item.position.clone(),
            Self::Integer(item) => item.position.clone(),
            Self::Match(item) => item.position.clone(),
            Self::Return(item) => item.position.clone(),
            Self::GetField(item) => item.position.clone(),
            Self::SetField(item) => item.position.clone(),
            Self::Use(item) => item.position.clone(),
            Self::While(item) => item.position.clone(),
            Self::String(item) => item.position.clone(),
        }
    }
}

pub struct Variable {
    pub position: Position,
    pub name: String,
}

impl From<parsed::Identifier> for Variable {
    fn from(identifier: parsed::Identifier) -> Self {
        Variable {
            position: identifier.position,
            name: identifier.value,
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

#[allow(dead_code)] // TODO #214 implement interfaces
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
    pub enum_: Rc<RefCell<Enum>>,
    pub type_parameters: Vec<Type>,
}

pub struct CallEnumConstructor {
    pub position: Position,
    pub enum_constructor: Rc<RefCell<EnumConstructor>>,

    #[allow(dead_code)] // TODO #221 Improve type parameter handling
    pub type_parameters: Vec<Type>,
}

pub struct CallFunction {
    pub position: Position,
    pub function: Rc<RefCell<Function>>,

    #[allow(dead_code)] // TODO #221 Improve type parameter handling
    pub type_parameters: Vec<Type>,
}

pub struct CallLocalVariable {
    pub position: Position,
    pub name: String,
}

pub struct CallStruct {
    pub position: Position,
    pub struct_: Rc<RefCell<Struct>>,
    pub type_parameters: Vec<Type>,
}

pub struct FunctionType {
    pub position: Position,
    pub argument_types: Vec<Type>,
    pub return_types: ReturnTypes,
}

pub struct GetFunction {
    pub position: Position,
    pub target: Rc<RefCell<Function>>,
}

pub struct Integer {
    pub position: Position,
    pub value: isize,
}

pub struct Match {
    pub position: Position,
    pub case_blocks: Vec<CaseBlock>,
    pub default_blocks: Vec<DefaultBlock>,
    pub target: Cell<Option<Rc<RefCell<Enum>>>>,
}

pub struct CaseBlock {
    pub position: Position,
    pub enum_name: String,
    pub variant_name: String,
    pub body: FunctionBody,
    pub variables: Vec<Variable>,
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
    pub target: Cell<Option<Rc<RefCell<Struct>>>>,
}

pub struct SetField {
    pub position: Position,
    pub field_name: String,
    pub body: FunctionBody,
    pub target: Cell<Option<Rc<RefCell<Struct>>>>,
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
    pub position: Position,
    pub value: String,
}

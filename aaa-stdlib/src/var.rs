use std::{
    cell::RefCell,
    collections::HashMap,
    fmt::{Debug, Formatter, Result},
    hash::Hash,
    rc::Rc,
    vec,
};

use crate::{
    hashtable::{HashTable, HashTableIterator},
    vector::{Vector, VectorIterator},
};

#[derive(PartialEq)]
pub struct Struct {
    // TODO consider using actual Rust types
    // instead of the hashmap approach
    pub type_name: String,
    pub values: HashMap<String, Variable>,
}

#[derive(Clone)]
pub enum Variable {
    None, // TODO get rid of this when iterators return an enum
    Integer(isize),
    Boolean(bool),
    String(Rc<RefCell<String>>), // TODO change to &str
    Vector(Rc<RefCell<Vector<Variable>>>),
    Set(Rc<RefCell<HashTable<Variable, ()>>>),
    Map(Rc<RefCell<HashTable<Variable, Variable>>>),
    Struct(Rc<RefCell<Struct>>),
    VectorIterator(Rc<RefCell<VectorIterator<Variable>>>),
    HashTableIterator(Rc<RefCell<HashTableIterator<Variable, Variable>>>),
    // TODO add iterators
    // TODO add enums
}

impl Variable {
    pub fn assign(&mut self, source: &Variable) {
        // TODO crash when source is in iterator or enum
        *self = source.clone();
    }
}

impl Debug for Variable {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        match self {
            Self::Boolean(v) => write!(f, "{}", v),
            Self::Integer(v) => write!(f, "{}", v),
            Self::String(v) => write!(f, "{}", (**v).borrow()),
            Self::Vector(v) => {
                let mut reprs: Vec<String> = vec![];
                for item in (**v).borrow_mut().iter() {
                    reprs.push(format!("{item:?}"))
                }
                write!(f, "[{}]", reprs.join(", "))
            }
            Self::Set(v) => {
                let mut reprs: Vec<String> = vec![];
                for item in (**v).borrow().iter() {
                    reprs.push(format!("{item:?}"))
                }
                write!(f, "{{{}}}", reprs.join(", "))
            }
            Self::Map(v) => {
                let mut reprs: Vec<String> = vec![];
                for (key, value) in (**v).borrow().iter() {
                    reprs.push(format!("{key:?}: {value:?}"))
                }
                write!(f, "{{{}}}", reprs.join(", "))
            }
            Self::Struct(v) => {
                let struct_ = (**v).borrow();
                write!(f, "(struct {})<{{", struct_.type_name)?;
                let mut reprs: Vec<String> = vec![];
                for (field_name, field_value) in struct_.values.iter() {
                    reprs.push(format!("{field_name:?}: {field_value:?}"));
                }
                write!(f, "{{{}}}>", reprs.join(", "))
            }
            Self::VectorIterator(_) => write!(f, "vec_iter"),
            Self::HashTableIterator(_) => write!(f, "map_iter"),
            Self::None => write!(f, "None"),
        }
    }
}

impl PartialEq for Variable {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Self::Integer(lhs), Self::Integer(rhs)) => lhs == rhs,
            (Self::Boolean(lhs), Self::Boolean(rhs)) => lhs == rhs,
            (Self::String(lhs), Self::String(rhs)) => lhs == rhs,
            (Self::Vector(lhs), Self::Vector(rhs)) => lhs == rhs,
            (Self::Set(lhs), Self::Set(rhs)) => lhs == rhs,
            (Self::Map(lhs), Self::Map(rhs)) => lhs == rhs,
            (Self::Struct(lhs), Self::Struct(rhs)) => lhs == rhs,
            _ => {
                todo!() // Can't compare variables of different types
            }
        }
    }
}

impl Eq for Variable {}

impl Hash for Variable {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        match self {
            Self::Boolean(v) => Hash::hash(&v, state),
            Self::Integer(v) => Hash::hash(&v, state),
            Self::String(v) => {
                let x = &(**v).as_ptr(); // TODO this probably does not work
                Hash::hash(x, state)
            }
            Self::Vector(_) => todo!(), // hashing is not implemented for this variant
            Self::Set(_) => todo!(),    // hashing is not implemented for this variant
            Self::Map(_) => todo!(),    // hashing is not implemented for this variant
            Self::Struct(_) => todo!(), // hashing is not implemented for this variant
            Self::None => todo!(),      // hashing is not implemented for this variant
            Self::VectorIterator(_) => todo!(), // hashing is not implemented for this variant
            Self::HashTableIterator(_) => todo!(), // hashing is not implemented for this variant
        }
    }
}

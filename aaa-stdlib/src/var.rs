use std::{
    cell::RefCell,
    collections::HashMap,
    fmt::{Debug, Display, Formatter, Result},
    hash::Hash,
    rc::Rc,
    vec,
};

use crate::{
    map::{Map, MapIterator},
    set::{Set, SetIterator},
    vector::{Vector, VectorIterator},
};

#[derive(PartialEq)]
pub struct Struct {
    pub type_name: String,
    pub values: HashMap<String, Variable>,
}

impl Debug for Struct {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        write!(f, "(struct {})<{{", self.type_name)?;
        let mut reprs: Vec<String> = vec![];
        for (field_name, field_value) in self.values.iter() {
            reprs.push(format!("{field_name:?}: {field_value:?}"));
        }
        write!(f, "{{{}}}>", reprs.join(", "))
    }
}

#[derive(Clone)]
pub enum Variable {
    None, // TODO get rid of this when Aaa iterators return an enum
    Integer(isize),
    Boolean(bool),
    String(Rc<RefCell<String>>),
    Vector(Rc<RefCell<Vector<Variable>>>), // TODO instead of Variable, use a type that has no Rc<...> so the container owns its values
    Set(Rc<RefCell<Set<Variable>>>), // TODO instead of Variable, use a type that has no Rc<...> so the container owns its values
    Map(Rc<RefCell<Map<Variable, Variable>>>), // TODO instead of Variable, use a type that has no Rc<...> so the container owns its values
    Struct(Rc<RefCell<Struct>>),
    VectorIterator(Rc<RefCell<VectorIterator<Variable>>>),
    MapIterator(Rc<RefCell<MapIterator<Variable, Variable>>>),
    SetIterator(Rc<RefCell<SetIterator<Variable>>>),
}

impl Variable {
    pub fn assign(&mut self, source: &Variable) {
        match *source {
            Self::MapIterator(_) | Self::SetIterator(_) | Self::VectorIterator(_) => {
                panic!("Cannot assign to an iterator!")
            }
            Self::None => panic!("Cannot assign to None!"),
            _ => (),
        }
        *self = source.clone();
    }
}

impl Display for Variable {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        match self {
            Self::Boolean(v) => write!(f, "{}", v),
            Self::Integer(v) => write!(f, "{}", v),
            Self::String(v) => write!(f, "{}", &*v.borrow()),
            Self::Vector(v) => write!(f, "{:?}", &*v.borrow()),
            Self::Set(v) => write!(f, "{}", &*v.borrow().fmt_as_set()),
            Self::Map(v) => write!(f, "{:?}", &*v.borrow()),
            Self::Struct(v) => write!(f, "{:?}", &*v.borrow()),
            Self::VectorIterator(_) => write!(f, "vec_iter"),
            Self::MapIterator(_) => write!(f, "map_iter"),
            Self::SetIterator(_) => write!(f, "set_iter"),
            Self::None => write!(f, "None"),
        }
    }
}

impl Debug for Variable {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        match self {
            Self::String(v) => write!(f, "{:?}", &*v.borrow()),
            _ => write!(f, "{}", self),
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
            Self::String(v) => Hash::hash(&*v.borrow().clone(), state),
            Self::Vector(_) => todo!(), // hashing is not implemented for this variant
            Self::Set(_) => todo!(),    // hashing is not implemented for this variant
            Self::Map(_) => todo!(),    // hashing is not implemented for this variant
            Self::Struct(_) => todo!(), // hashing is not implemented for this variant
            Self::None => todo!(),      // hashing is not implemented for this variant
            Self::VectorIterator(_) => todo!(), // hashing is not implemented for this variant
            Self::MapIterator(_) => todo!(), // hashing is not implemented for this variant
            Self::SetIterator(_) => todo!(), // hashing is not implemented for this variant
        }
    }
}

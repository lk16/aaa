use std::{
    cell::RefCell,
    fmt::{Debug, Formatter, Result},
    hash::Hash,
    rc::Rc,
    vec,
};

use crate::{
    map::{Map, MapIterator},
    set::{Set, SetIterator},
    stack::VariableEnum,
    vector::{Vector, VectorIterator},
};

#[derive(Clone)]
pub enum Variable<T>
where
    T: Debug + Clone + PartialEq + Eq + Hash,
{
    None, // TODO get rid of this when Aaa iterators return an enum
    Integer(isize),
    Boolean(bool),
    String(Rc<RefCell<String>>),                  // TODO change to &str
    Vector(Rc<RefCell<Vector<VariableEnum<T>>>>), // TODO instead of VariableEnum<T>, use a type that has no Rc<...> so the container owns its values
    Set(Rc<RefCell<Set<VariableEnum<T>>>>), // TODO instead of VariableEnum<T>, use a type that has no Rc<...> so the container owns its values
    Map(Rc<RefCell<Map<VariableEnum<T>, VariableEnum<T>>>>), // TODO instead of VariableEnum<T>, use a type that has no Rc<...> so the container owns its values
    VectorIterator(Rc<RefCell<VectorIterator<VariableEnum<T>>>>),
    MapIterator(Rc<RefCell<MapIterator<VariableEnum<T>, VariableEnum<T>>>>),
    SetIterator(Rc<RefCell<SetIterator<VariableEnum<T>>>>),
}

impl<T> Variable<T>
where
    T: Debug + Clone + PartialEq + Eq + Hash,
{
    pub fn assign(&mut self, source: &Variable<T>) {
        // TODO crash when source is in iterator or enum
        *self = source.clone();
    }
}

impl<T> Debug for Variable<T>
where
    T: Debug + Clone + PartialEq + Eq + Hash,
{
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        match self {
            Self::Boolean(v) => write!(f, "{}", v),
            Self::Integer(v) => write!(f, "{}", v),
            Self::String(v) => write!(f, "{}", (**v).borrow()),
            Self::Vector(v) => write!(f, "{v:?}"),
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
            Self::VectorIterator(_) => write!(f, "vec_iter"),
            Self::MapIterator(_) => write!(f, "map_iter"),
            Self::SetIterator(_) => write!(f, "set_iter"),
            Self::None => write!(f, "None"),
        }
    }
}

impl<T> PartialEq for Variable<T>
where
    T: Debug + Clone + PartialEq + Eq + Hash,
{
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Self::Integer(lhs), Self::Integer(rhs)) => lhs == rhs,
            (Self::Boolean(lhs), Self::Boolean(rhs)) => lhs == rhs,
            (Self::String(lhs), Self::String(rhs)) => lhs == rhs,
            (Self::Vector(lhs), Self::Vector(rhs)) => lhs == rhs,
            (Self::Set(lhs), Self::Set(rhs)) => lhs == rhs,
            (Self::Map(lhs), Self::Map(rhs)) => lhs == rhs,
            _ => {
                todo!() // Can't compare variables of different types
            }
        }
    }
}

impl<T> Eq for Variable<T> where T: Debug + Clone + PartialEq + Eq + Hash {}

impl<T> Hash for Variable<T>
where
    T: Debug + Clone + PartialEq + Eq + Hash,
{
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
            Self::None => todo!(),      // hashing is not implemented for this variant
            Self::VectorIterator(_) => todo!(), // hashing is not implemented for this variant
            Self::MapIterator(_) => todo!(), // hashing is not implemented for this variant
            Self::SetIterator(_) => todo!(), // hashing is not implemented for this variant
        }
    }
}

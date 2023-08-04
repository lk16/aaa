use std::{
    cell::RefCell,
    fmt::{Debug, Display, Formatter, Result},
    hash::Hash,
    rc::Rc,
};

use regex::Regex;

use crate::{
    map::{Map, MapIterator},
    set::{Set, SetIterator, SetValue},
    vector::{Vector, VectorIterator},
};

pub trait UserType: Clone + Debug + Display + Hash + PartialEq {
    fn kind(&self) -> String;
    fn clone_recursive(&self) -> Self;
}

#[derive(Clone)]
pub enum Variable<T>
where
    T: UserType,
{
    None, // TODO #33 Remove when iterators return an enum
    Integer(isize),
    Boolean(bool),
    String(Rc<RefCell<String>>),
    Vector(Rc<RefCell<Vector<Variable<T>>>>),
    Set(Rc<RefCell<Set<Variable<T>>>>),
    Map(Rc<RefCell<Map<Variable<T>, Variable<T>>>>),
    VectorIterator(Rc<RefCell<VectorIterator<Variable<T>>>>),
    MapIterator(Rc<RefCell<MapIterator<Variable<T>, Variable<T>>>>),
    SetIterator(Rc<RefCell<SetIterator<Variable<T>>>>),
    Regex(Rc<RefCell<Regex>>),
    UserType(Rc<RefCell<T>>),
}

impl<T> Variable<T>
where
    T: UserType,
{
    pub fn assign(&mut self, source: &Variable<T>) {
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

impl<T> UserType for Variable<T>
where
    T: UserType,
{
    fn kind(&self) -> String {
        match self {
            Self::None => String::from("none"),
            Self::Integer(_) => String::from("int"),
            Self::Boolean(_) => String::from("bool"),
            Self::String(_) => String::from("str"),
            Self::Vector(_) => String::from("vec"),
            Self::Set(_) => String::from("set"),
            Self::Map(_) => String::from("map"),
            Self::VectorIterator(_) => String::from("vec_iter"),
            Self::MapIterator(_) => String::from("map_iter"),
            Self::SetIterator(_) => String::from("set_iter"),
            Self::Regex(_) => String::from("regex"),
            Self::UserType(v) => (**v).borrow().kind(),
        }
    }

    // Does not copy references, but copies recursively
    fn clone_recursive(&self) -> Self {
        // TODO #35 prevent infinite recursion.
        match self {
            Self::None => Self::None,
            Self::Integer(v) => Self::Integer(*v),
            Self::Boolean(v) => Self::Boolean(*v),
            Self::String(v) => {
                let string = (**v).borrow().clone();
                Self::String(Rc::new(RefCell::new(string)))
            }
            Self::Vector(v) => {
                let mut cloned = Vector::new();
                let source = (**v).borrow();
                for item in source.iter() {
                    cloned.push(item.clone_recursive())
                }
                Self::Vector(Rc::new(RefCell::new(cloned)))
            }
            Self::Set(v) => {
                let mut cloned = Map::new();
                let source = (**v).borrow();
                for (item, _) in source.iter() {
                    cloned.insert(item.clone_recursive(), SetValue);
                }
                Self::Set(Rc::new(RefCell::new(cloned)))
            }
            Self::Map(v) => {
                let mut cloned = Map::new();
                let source = (**v).borrow();
                for (key, value) in source.iter() {
                    cloned.insert(key.clone_recursive(), value.clone_recursive());
                }
                Self::Map(Rc::new(RefCell::new(cloned)))
            }
            Self::VectorIterator(_) | Self::MapIterator(_) | Self::SetIterator(_) => {
                unreachable!(); // Cannot recursively clone an iterator
            }
            Self::Regex(regex) => Self::Regex(regex.clone()),
            Self::UserType(v) => {
                let cloned = (**v).borrow().clone_recursive();
                Self::UserType(Rc::new(RefCell::new(cloned)))
            }
        }
    }
}

impl<T> Display for Variable<T>
where
    T: UserType,
{
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        match self {
            Self::Boolean(v) => write!(f, "{}", v),
            Self::Integer(v) => write!(f, "{}", v),
            Self::String(v) => write!(f, "{}", (**v).borrow()),
            Self::Vector(v) => write!(f, "{}", (**v).borrow()),
            Self::Set(v) => write!(f, "{}", (**v).borrow().fmt_as_set()),
            Self::Map(v) => write!(f, "{}", (**v).borrow()),
            Self::VectorIterator(_) => write!(f, "vec_iter"),
            Self::MapIterator(_) => write!(f, "map_iter"),
            Self::SetIterator(_) => write!(f, "set_iter"),
            Self::None => write!(f, "None"),
            Self::Regex(_) => write!(f, "regex"),
            Self::UserType(v) => write!(f, "{}", (**v).borrow()),
        }
    }
}

impl<T> Debug for Variable<T>
where
    T: UserType,
{
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        match self {
            Self::String(v) => write!(f, "{:?}", (**v).borrow()),
            _ => write!(f, "{}", self),
        }
    }
}

impl<T> PartialEq for Variable<T>
where
    T: UserType,
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
                unreachable!() // Can't compare variables of different types
            }
        }
    }
}

impl<T> Eq for Variable<T> where T: UserType {}

impl<T> Hash for Variable<T>
where
    T: UserType,
{
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        match self {
            Self::Boolean(v) => Hash::hash(&v, state),
            Self::Integer(v) => Hash::hash(&v, state),
            Self::String(v) => {
                let string = (**v).borrow().clone();
                Hash::hash(&string, state)
            }
            _ => {
                unreachable!() // Can't hash variables of different types
            }
        }
    }
}

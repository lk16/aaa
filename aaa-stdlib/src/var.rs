use std::{
    borrow::Borrow,
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

#[derive(PartialEq, Clone)]
pub struct Struct {
    pub type_name: String,
    pub values: HashMap<String, Variable>,
}

impl Debug for Struct {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        write!(f, "(struct {})<", self.type_name)?;
        let mut reprs: Vec<String> = vec![];
        for (field_name, field_value) in self.values.iter() {
            reprs.push(format!("{field_name:?}: {field_value:?}"));
        }
        write!(f, "{{{}}}>", reprs.join(", "))
    }
}

impl Hash for Struct {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        todo!()
    }
}

#[derive(Clone, PartialEq, Hash)]
pub struct Enum {
    pub type_name: String,
    pub discriminant: usize,
    pub value: Variable,
}

impl Debug for Enum {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        write!(
            f,
            "(enum {} discriminant={})<{:?}>",
            self.type_name,
            self.discriminant,
            self.value.borrow()
        )
    }
}

#[derive(Hash, Debug, PartialEq, Clone)]
pub enum ContainerValue {
    Integer(isize),
    Boolean(bool),
    String(String),
    Vector(Vector<ContainerValue>),
    Set(Set<ContainerValue>),
    Map(Map<ContainerValue, ContainerValue>),
    Struct(Struct),
    Enum(Enum),
}

impl From<Variable> for ContainerValue {
    fn from(var: Variable) -> ContainerValue {
        match var {
            Variable::None => todo!(), // Not supported
            Variable::Integer(v) => ContainerValue::Integer(v),
            Variable::Boolean(v) => ContainerValue::Boolean(v),
            Variable::String(v) => ContainerValue::String((*v).borrow().clone()),
            Variable::Vector(v) => todo!(),         // TODO conversion
            Variable::Set(v) => todo!(),            // TODO conversion
            Variable::Map(v) => todo!(),            // TODO conversion
            Variable::Struct(v) => todo!(),         // TODO conversion
            Variable::VectorIterator(_) => todo!(), // Not supported
            Variable::MapIterator(_) => todo!(),    // Not supported
            Variable::SetIterator(_) => todo!(),    // Not supported
            Variable::Enum(v) => ContainerValue::Enum(*v.borrow().clone()),
        }
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
    Enum(Rc<RefCell<Enum>>),
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

    pub fn kind(&self) -> String {
        match self {
            Self::None => String::from("none"),
            Self::Integer(_) => String::from("int"),
            Self::Boolean(_) => String::from("bool"),
            Self::String(_) => String::from("str"),
            Self::Vector(_) => String::from("vec"),
            Self::Set(_) => String::from("set"),
            Self::Map(_) => String::from("map"),
            Self::Struct(s) => {
                let type_name = &(**s).borrow().type_name;
                String::from(format!("(struct {type_name})"))
            }
            Self::VectorIterator(_) => String::from("vec_iter"),
            Self::MapIterator(_) => String::from("map_iter"),
            Self::SetIterator(_) => String::from("set_iter"),
            Self::Enum(e) => {
                let type_name = &(**e).borrow().type_name;
                String::from(format!("(enum {type_name})"))
            }
        }
    }

    // Does not copy references, but copies recursively
    pub fn clone_recursive(&self) -> Self {
        // TODO prevent infinite recursion.
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
                    cloned.insert(item.clone_recursive(), ());
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
            Self::Struct(_v) => todo!(),
            Self::Enum(_v) => todo!(),
            Self::VectorIterator(_) | Self::MapIterator(_) | Self::SetIterator(_) => {
                todo!(); // Cannot recursively clone an iterator
            }
        }
    }
}

impl Display for Variable {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        match self {
            Self::Boolean(v) => write!(f, "{}", v),
            Self::Integer(v) => write!(f, "{}", v),
            Self::String(v) => write!(f, "{}", (**v).borrow()),
            Self::Vector(v) => write!(f, "{:?}", (**v).borrow()),
            Self::Set(v) => write!(f, "{}", (**v).borrow().fmt_as_set()),
            Self::Map(v) => write!(f, "{:?}", (**v).borrow()),
            Self::Struct(v) => write!(f, "{:?}", (**v).borrow()),
            Self::VectorIterator(_) => write!(f, "vec_iter"),
            Self::MapIterator(_) => write!(f, "map_iter"),
            Self::SetIterator(_) => write!(f, "set_iter"),
            Self::None => write!(f, "None"),
            Self::Enum(v) => write!(f, "{:?}", (**v).borrow()),
        }
    }
}

impl Debug for Variable {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        match self {
            Self::String(v) => write!(f, "{:?}", (**v).borrow()),
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
            (Self::Enum(lhs), Self::Enum(rhs)) => lhs == rhs,
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
                let string = (**v).borrow().clone();
                Hash::hash(&string, state)
            }
            Self::Vector(_) => todo!(), // hashing is not implemented for this variant
            Self::Set(_) => todo!(),    // hashing is not implemented for this variant
            Self::Map(_) => todo!(),    // hashing is not implemented for this variant
            Self::Struct(_) => todo!(), // hashing is not implemented for this variant
            Self::None => todo!(),      // hashing is not implemented for this variant
            Self::VectorIterator(_) => todo!(), // hashing is not implemented for this variant
            Self::MapIterator(_) => todo!(), // hashing is not implemented for this variant
            Self::SetIterator(_) => todo!(), // hashing is not implemented for this variant
            Self::Enum(_) => todo!(),   // hashing is not implemented for this variant
        }
    }
}

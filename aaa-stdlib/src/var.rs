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

#[derive(Clone)]
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
        for (key, value) in self.values.iter() {
            Hash::hash(&key, state);
            Hash::hash(&value, state);
        }
    }
}

impl PartialEq for Struct {
    fn eq(&self, other: &Self) -> bool {
        self.type_name == other.type_name && self.values == other.values
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

#[derive(Hash, PartialEq, Clone)]
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

impl ContainerValue {
    pub fn kind(&self) -> String {
        let var: Variable = self.clone().into();
        var.kind()
    }
}

impl Display for ContainerValue {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        let var: Variable = self.clone().into();
        write!(f, "{}", var)
    }
}

impl Debug for ContainerValue {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        let var: Variable = self.clone().into();
        write!(f, "{:?}", var)
    }
}

impl From<Variable> for ContainerValue {
    fn from(var: Variable) -> ContainerValue {
        match var {
            Variable::Integer(v) => ContainerValue::Integer(v),
            Variable::Boolean(v) => ContainerValue::Boolean(v),
            Variable::String(v) => ContainerValue::String((*v).borrow().clone()),
            Variable::Vector(v) => ContainerValue::Vector((*v).borrow().clone()),
            Variable::Set(v) => ContainerValue::Set((*v).borrow().clone()),
            Variable::Map(v) => ContainerValue::Map((*v).borrow().clone()),
            Variable::Struct(v) => ContainerValue::Struct((*v).borrow().clone()),
            Variable::Enum(v) => ContainerValue::Enum((*v).borrow().clone()),
            _ => {
                let kind = var.kind();
                panic!("Cannot convert {} to container value", kind);
            }
        }
    }
}

#[derive(Clone)]
pub enum Variable {
    None, // TODO get rid of this when Aaa iterators return an enum
    Integer(isize),
    Boolean(bool),
    String(Rc<RefCell<String>>),
    Vector(Rc<RefCell<Vector<ContainerValue>>>),
    Set(Rc<RefCell<Set<ContainerValue>>>),
    Map(Rc<RefCell<Map<ContainerValue, ContainerValue>>>),
    Struct(Rc<RefCell<Struct>>),
    VectorIterator(Rc<RefCell<VectorIterator<ContainerValue>>>),
    MapIterator(Rc<RefCell<MapIterator<ContainerValue, ContainerValue>>>),
    SetIterator(Rc<RefCell<SetIterator<ContainerValue>>>),
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
                format!("(struct {type_name})")
            }
            Self::VectorIterator(_) => String::from("vec_iter"),
            Self::MapIterator(_) => String::from("map_iter"),
            Self::SetIterator(_) => String::from("set_iter"),
            Self::Enum(e) => {
                let type_name = &(**e).borrow().type_name;
                format!("(enum {type_name})")
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
                    cloned.push(item.clone())
                }
                Self::Vector(Rc::new(RefCell::new(cloned)))
            }
            Self::Set(v) => {
                let mut cloned = Map::new();
                let source = (**v).borrow();
                for (item, _) in source.iter() {
                    cloned.insert(item.clone(), ());
                }
                Self::Set(Rc::new(RefCell::new(cloned)))
            }
            Self::Map(v) => {
                let mut cloned = Map::new();
                let source = (**v).borrow();
                for (key, value) in source.iter() {
                    cloned.insert(key.clone(), value.clone());
                }
                Self::Map(Rc::new(RefCell::new(cloned)))
            }
            Self::Struct(_v) => todo!(),
            Self::Enum(_v) => todo!(),
            Self::VectorIterator(_) | Self::MapIterator(_) | Self::SetIterator(_) => {
                unreachable!(); // Cannot recursively clone an iterator
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
                unreachable!() // Can't compare variables of different types
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
            Self::Vector(_) => unreachable!(),
            Self::Set(_) => unreachable!(),
            Self::Map(_) => unreachable!(),
            Self::Struct(_) => unreachable!(),
            Self::None => unreachable!(),
            Self::VectorIterator(_) => unreachable!(),
            Self::MapIterator(_) => unreachable!(),
            Self::SetIterator(_) => unreachable!(),
            Self::Enum(_) => unreachable!(),
        }
    }
}

impl From<ContainerValue> for Variable {
    fn from(val: ContainerValue) -> Variable {
        match val {
            ContainerValue::Integer(v) => Variable::Integer(v),
            ContainerValue::Boolean(v) => Variable::Boolean(v),
            ContainerValue::String(v) => Variable::String(Rc::new(RefCell::new(v))),
            ContainerValue::Vector(v) => Variable::Vector(Rc::new(RefCell::new(v))),
            ContainerValue::Set(v) => Variable::Set(Rc::new(RefCell::new(v))),
            ContainerValue::Map(v) => Variable::Map(Rc::new(RefCell::new(v))),
            ContainerValue::Struct(v) => Variable::Struct(Rc::new(RefCell::new(v))),
            ContainerValue::Enum(v) => Variable::Enum(Rc::new(RefCell::new(v))),
        }
    }
}

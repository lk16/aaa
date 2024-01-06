use std::{
    cell::RefCell,
    fmt::{Debug, Display, Formatter, Result},
    hash::Hash,
    mem,
    rc::Rc,
};

use regex::Regex;

use crate::{
    map::{Map, MapIterator},
    set::{Set, SetIterator, SetValue},
    stack::Stack,
    vector::{Vector, VectorIterator},
};

pub trait UserType: Clone + Debug + Display + Hash + PartialEq + Eq {
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
    Character(char),
    String(Rc<RefCell<String>>),
    Vector(Rc<RefCell<Vector<Variable<T>>>>),
    Set(Rc<RefCell<Set<Variable<T>>>>),
    Map(Rc<RefCell<Map<Variable<T>, Variable<T>>>>),
    VectorIterator(Rc<RefCell<VectorIterator<Variable<T>>>>),
    MapIterator(Rc<RefCell<MapIterator<Variable<T>, Variable<T>>>>),
    SetIterator(Rc<RefCell<SetIterator<Variable<T>>>>),
    Regex(Rc<RefCell<Regex>>),
    FunctionPointer(fn(&mut Stack<T>)),
    UserType(Rc<RefCell<T>>),
}

impl<T> Variable<T>
where
    T: UserType,
{
    pub fn assign(&mut self, source: &mut Variable<T>) {
        if mem::discriminant(&self) != mem::discriminant(&source) {
            panic!("Attempt to change variable type in assignment")
        }

        match *source {
            Self::MapIterator(_) | Self::SetIterator(_) | Self::VectorIterator(_) => {
                panic!("Cannot assign to an iterator!")
            }
            Self::None => panic!("Cannot assign to None!"),
            _ => (),
        }
        *self = source.clone();
    }

    pub fn integer_zero_value() -> Variable<T> {
        Variable::Integer(0)
    }

    pub fn boolean_zero_value() -> Variable<T> {
        Variable::Boolean(false)
    }

    pub fn character_zero_value() -> Variable<T> {
        Variable::Character('\0')
    }

    pub fn string_zero_value() -> Variable<T> {
        Variable::String(Rc::new(RefCell::new(String::from(""))))
    }

    pub fn vector_zero_value() -> Variable<T> {
        Variable::Vector(Rc::new(RefCell::new(Vector::new())))
    }

    pub fn set_zero_value() -> Variable<T> {
        Variable::Set(Rc::new(RefCell::new(Set::new())))
    }

    pub fn map_zero_value() -> Variable<T> {
        Variable::Map(Rc::new(RefCell::new(Map::new())))
    }

    pub fn regex_zero_value() -> Variable<T> {
        Variable::Regex(Rc::new(RefCell::new(Regex::new("$.^").unwrap())))
    }

    pub fn function_pointer_zero_value() -> Variable<T> {
        Variable::FunctionPointer(Stack::zero_function_pointer_value)
    }

    pub fn get_integer(&self) -> isize {
        match self {
            Self::Integer(v) => *v,
            _ => unreachable!(),
        }
    }

    pub fn get_boolean(&self) -> bool {
        match self {
            Self::Boolean(v) => *v,
            _ => unreachable!(),
        }
    }

    pub fn get_string(&self) -> Rc<RefCell<String>> {
        match self {
            Self::String(v) => v.clone(),
            _ => unreachable!(),
        }
    }

    pub fn get_vector(&self) -> Rc<RefCell<Vector<Variable<T>>>> {
        match self {
            Self::Vector(v) => v.clone(),
            _ => unreachable!(),
        }
    }

    pub fn get_set(&self) -> Rc<RefCell<Set<Variable<T>>>> {
        match self {
            Self::Set(v) => v.clone(),
            _ => unreachable!(),
        }
    }

    pub fn get_map(&self) -> Rc<RefCell<Map<Variable<T>, Variable<T>>>> {
        match self {
            Self::Map(v) => v.clone(),
            _ => unreachable!(),
        }
    }

    pub fn get_vector_iterator(&self) -> Rc<RefCell<VectorIterator<Variable<T>>>> {
        match self {
            Self::VectorIterator(v) => v.clone(),
            _ => unreachable!(),
        }
    }

    pub fn get_map_iterator(&self) -> Rc<RefCell<MapIterator<Variable<T>, Variable<T>>>> {
        match self {
            Self::MapIterator(v) => v.clone(),
            _ => unreachable!(),
        }
    }

    pub fn get_set_iterator(&self) -> Rc<RefCell<SetIterator<Variable<T>>>> {
        match self {
            Self::SetIterator(v) => v.clone(),
            _ => unreachable!(),
        }
    }

    pub fn get_regex(&self) -> Rc<RefCell<Regex>> {
        match self {
            Self::Regex(v) => v.clone(),
            _ => unreachable!(),
        }
    }

    pub fn get_function_pointer(&self) -> fn(&mut Stack<T>) {
        match self {
            Self::FunctionPointer(v) => v.clone(),
            _ => unreachable!(),
        }
    }

    pub fn get_usertype(&self) -> Rc<RefCell<T>> {
        match self {
            Self::UserType(v) => v.clone(),
            _ => unreachable!(),
        }
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
            Self::Character(_) => String::from("char"),
            Self::String(_) => String::from("str"),
            Self::Vector(_) => String::from("vec"),
            Self::Set(_) => String::from("set"),
            Self::Map(_) => String::from("map"),
            Self::VectorIterator(_) => String::from("vec_iter"),
            Self::MapIterator(_) => String::from("map_iter"),
            Self::SetIterator(_) => String::from("set_iter"),
            Self::Regex(_) => String::from("regex"),
            Self::FunctionPointer(_) => String::from("fn_ptr"),
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
            Self::Character(v) => Self::Character(*v),
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
            Self::FunctionPointer(v) => Self::FunctionPointer(v.clone()),
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
            Self::Character(v) => write!(f, "{}", v),
            Self::Vector(v) => write!(f, "{}", (**v).borrow()),
            Self::Set(v) => write!(f, "{}", (**v).borrow().fmt_as_set()),
            Self::Map(v) => write!(f, "{}", (**v).borrow()),
            Self::VectorIterator(_) => write!(f, "vec_iter"),
            Self::MapIterator(_) => write!(f, "map_iter"),
            Self::SetIterator(_) => write!(f, "set_iter"),
            Self::None => write!(f, "None"),
            Self::Regex(_) => write!(f, "regex"),
            Self::FunctionPointer(_) => write!(f, "func_ptr"),
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
            (Self::Character(lhs), Self::Character(rhs)) => lhs == rhs,
            (Self::String(lhs), Self::String(rhs)) => lhs == rhs,
            (Self::Vector(lhs), Self::Vector(rhs)) => lhs == rhs,
            (Self::Set(lhs), Self::Set(rhs)) => lhs == rhs,
            (Self::Map(lhs), Self::Map(rhs)) => lhs == rhs,
            (Self::Regex(lhs), Self::Regex(rhs)) => {
                let lhs_ref = lhs.borrow();
                let rhs_ref = rhs.borrow();
                lhs_ref.as_str() == rhs_ref.as_str()
            }
            (Self::FunctionPointer(lhs), Self::FunctionPointer(rhs)) => lhs == rhs,
            (Self::UserType(lhs), Self::UserType(rhs)) => lhs == rhs,
            _ => unreachable!(), // Can't compare variables of different types
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
            Self::Character(v) => Hash::hash(&v, state),
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

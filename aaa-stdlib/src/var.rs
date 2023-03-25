use std::{
    cell::RefCell,
    collections::{HashMap, HashSet},
    fmt::{Debug, Formatter, Result},
    rc::Rc,
};

#[derive(Clone)]
pub enum Variable {
    Integer(isize),
    Boolean(bool),
    String(Rc<RefCell<String>>),
    Vector(Rc<RefCell<Vec<Variable>>>),
    Set(Rc<RefCell<HashSet<Variable>>>),
    Map(Rc<RefCell<HashMap<Variable, Variable>>>),
    // TODO add iterators
    // TODO add enums
}

impl Debug for Variable {
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        match self {
            Self::Boolean(v) => write!(f, "{}", v),
            Self::Integer(v) => write!(f, "{}", v),
            Self::String(v) => write!(f, "{}", v.borrow()),
            Self::Vector(v) => {
                let mut reprs: Vec<String> = vec![];
                for item in v.borrow().iter() {
                    reprs.push(format!("{item:?}"))
                }
                write!(f, "[{}]", reprs.join(", "))
            }
            Self::Set(v) => {
                let mut reprs: Vec<String> = vec![];
                for item in v.borrow().iter() {
                    reprs.push(format!("{item:?}"))
                }
                write!(f, "{{{}}}", reprs.join(", "))
            }
            Self::Map(v) => {
                let mut reprs: Vec<String> = vec![];
                for (key, value) in v.borrow().iter() {
                    reprs.push(format!("{key:?}: {value:?}"))
                }
                write!(f, "{{{}}}", reprs.join(", "))
            }
        }
    }
}

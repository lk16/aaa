// TODO remove
#![allow(dead_code)]
#![allow(unused_variables)]
#![allow(unreachable_code)]

use std::{
    collections::{HashMap, HashSet},
    rc::Rc,
};

use crate::var::Variable;

pub struct Stack {
    items: Vec<Variable>,
}

impl Stack {
    pub fn new() -> Self {
        Self { items: Vec::new() }
    }

    pub fn push_int(&mut self, v: isize) {
        let item = Variable::Integer(v);
        self.items.push(item)
    }

    pub fn push_bool(&mut self, v: bool) {
        let item = Variable::Boolean(v);
        self.items.push(item)
    }

    pub fn push_str(&mut self, v: String) {
        let item = Variable::String(Rc::new(v));
        self.items.push(item)
    }

    pub fn push_vector(&mut self, v: Vec<Variable>) {
        let item = Variable::Vector(Rc::new(v));
        self.items.push(item)
    }

    pub fn push_set(&mut self, v: HashSet<Variable>) {
        let item = Variable::Set(Rc::new(v));
        self.items.push(item)
    }

    pub fn push_map(&mut self, v: HashMap<Variable, Variable>) {
        let item = Variable::Map(Rc::new(v));
        self.items.push(item)
    }

    fn pop(&mut self) -> Variable {
        match self.items.pop() {
            Some(popped) => popped,
            None => todo!(), // TODO handle popping from empty stack
        }
    }

    pub fn pop_int(&mut self) -> isize {
        match self.pop() {
            Variable::Integer(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_bool(&mut self) -> bool {
        match self.pop() {
            Variable::Boolean(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_str(&mut self) -> Rc<String> {
        match self.pop() {
            Variable::String(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_vector(&mut self) -> Rc<Vec<Variable>> {
        match self.pop() {
            Variable::Vector(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_set(&mut self) -> Rc<HashSet<Variable>> {
        match self.pop() {
            Variable::Set(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn pop_map(&mut self) -> Rc<HashMap<Variable, Variable>> {
        match self.pop() {
            Variable::Map(v) => v,
            _ => todo!(), // TODO handle type error
        }
    }

    pub fn print_top(&mut self) {
        let top = self.pop();
        print!("{top:?}")
    }
}

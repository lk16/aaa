use std::{cell::RefCell, fmt::Display, hash::Hash, rc::Rc};

use crate::var::UserType;

pub struct Vector<T>
where
    T: UserType,
{
    vec: Rc<RefCell<Vec<T>>>,
    iterator_count: Rc<RefCell<usize>>, // vector can only be modified if no iterators exist
}

impl<T> Vector<T>
where
    T: UserType,
{
    pub fn new() -> Self {
        Self {
            vec: Rc::new(RefCell::new(vec![])),
            iterator_count: Rc::new(RefCell::new(0)),
        }
    }

    pub fn push(&mut self, item: T) {
        self.detect_invalid_change();
        self.vec.borrow_mut().push(item);
    }

    pub fn pop(&mut self) -> Option<T> {
        self.detect_invalid_change();
        self.vec.borrow_mut().pop()
    }

    pub fn len(&self) -> usize {
        self.vec.borrow().len()
    }

    pub fn is_empty(&self) -> bool {
        self.vec.borrow().is_empty()
    }

    pub fn clear(&mut self) {
        self.detect_invalid_change();
        self.vec.borrow_mut().clear();
    }

    pub fn iter(&self) -> VectorIterator<T> {
        VectorIterator::new(self.vec.clone(), self.iterator_count.clone())
    }

    pub fn get(&self, index: usize) -> T {
        self.vec.borrow()[index].clone()
    }

    pub fn set(&mut self, index: usize, item: T) {
        self.detect_invalid_change();
        self.vec.borrow_mut()[index] = item;
    }

    fn detect_invalid_change(&self) {
        if *self.iterator_count.borrow() != 0 {
            panic!("Vector does not allow changes! This probably means it is being iterated over.");
        }
    }
}

impl<T> From<Vec<T>> for Vector<T>
where
    T: UserType,
{
    fn from(value: Vec<T>) -> Self {
        let vec = Self::new();

        {
            let mut inner = vec.vec.borrow_mut();
            for item in value {
                inner.push(item);
            }
        } // be sure borrow ends here

        vec
    }
}

impl<T> Display for Vector<T>
where
    T: UserType,
{
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let mut reprs: Vec<String> = vec![];
        for item in self.iter() {
            reprs.push(format!("{item:?}"))
        }
        write!(f, "[{}]", reprs.join(", "))
    }
}

impl<T> PartialEq for Vector<T>
where
    T: UserType,
{
    fn eq(&self, other: &Self) -> bool {
        self.vec == other.vec
    }
}

impl<T> Eq for Vector<T> where T: UserType {}

impl<T> Clone for Vector<T>
where
    T: UserType,
{
    fn clone(&self) -> Self {
        let mut cloned = Vector::<T>::new();
        for item in self.iter() {
            cloned.push(item);
        }

        cloned
    }
}

impl<T> Hash for Vector<T>
where
    T: UserType,
{
    fn hash<H: std::hash::Hasher>(&self, _state: &mut H) {
        unreachable!()
    }
}

impl<T> Default for Vector<T>
where
    T: UserType,
{
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Clone)]
pub struct VectorIterator<T>
where
    T: UserType,
{
    vector: Rc<RefCell<Vec<T>>>,
    iterator_count: Rc<RefCell<usize>>,
    offset: usize,
}

impl<T> VectorIterator<T>
where
    T: UserType,
{
    pub fn new(vector: Rc<RefCell<Vec<T>>>, iterator_count: Rc<RefCell<usize>>) -> Self {
        *iterator_count.borrow_mut() += 1;

        Self {
            vector,
            iterator_count,
            offset: 0,
        }
    }

    pub fn clone_recursive(&self) -> Self {
        unreachable!() // TODO
    }
}

impl<T> Iterator for VectorIterator<T>
where
    T: UserType,
{
    type Item = T;

    fn next(&mut self) -> Option<Self::Item> {
        let vector = self.vector.borrow();
        let item = vector.get(self.offset).cloned();
        self.offset += 1;

        item
    }
}

impl<T> Drop for VectorIterator<T>
where
    T: UserType,
{
    fn drop(&mut self) {
        *self.iterator_count.borrow_mut() -= 1;
    }
}

impl<T> Display for VectorIterator<T>
where
    T: UserType,
{
    fn fmt(&self, _f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        unreachable!() // TODO
    }
}

impl<T> PartialEq for VectorIterator<T>
where
    T: UserType,
{
    fn eq(&self, _other: &Self) -> bool {
        unreachable!() // TODO
    }
}

impl<T> Eq for VectorIterator<T> where T: UserType {}

use std::{cell::RefCell, rc::Rc};

pub struct Vector<T>
where
    T: Clone + PartialEq,
{
    vec: Rc<RefCell<Vec<T>>>,
    iterator_count: Rc<RefCell<usize>>, // vector can only be modified if no iterators exist
}

impl<T: Clone + PartialEq> Vector<T> {
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

impl<T: Clone + PartialEq> From<Vec<T>> for Vector<T> {
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

impl<T: Clone + PartialEq> PartialEq for Vector<T> {
    fn eq(&self, other: &Self) -> bool {
        self.vec == other.vec
    }
}

#[derive(Clone)]
pub struct VectorIterator<T>
where
    T: Clone,
{
    vector: Rc<RefCell<Vec<T>>>,
    iterator_count: Rc<RefCell<usize>>,
    offset: usize,
}

impl<T> VectorIterator<T>
where
    T: Clone,
{
    fn new(vector: Rc<RefCell<Vec<T>>>, iterator_count: Rc<RefCell<usize>>) -> Self {
        *iterator_count.borrow_mut() += 1;

        Self {
            vector,
            iterator_count,
            offset: 0,
        }
    }
}

impl<T> Iterator for VectorIterator<T>
where
    T: Clone,
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
    T: Clone,
{
    fn drop(&mut self) {
        *self.iterator_count.borrow_mut() -= 1;
    }
}

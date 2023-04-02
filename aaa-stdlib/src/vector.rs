use std::{cell::RefCell, rc::Rc};

#[derive(Clone)]
pub struct VectorIterator<T>
where
    T: Clone,
{
    vector: Rc<RefCell<Vec<T>>>,
    offset: usize,
}

impl<T: Clone> VectorIterator<T> {
    pub fn new(vector: Rc<RefCell<Vec<T>>>) -> Self {
        Self { vector, offset: 0 }
    }
}

impl<T: Clone> Iterator for VectorIterator<T> {
    type Item = T;

    fn next(&mut self) -> Option<Self::Item> {
        let vector = self.vector.borrow();
        let item = vector.get(self.offset).cloned();
        self.offset += 1;

        item
    }
}

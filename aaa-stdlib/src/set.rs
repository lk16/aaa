use crate::map::{HashTableIterator, Map};

pub type Set<T> = Map<T, ()>;

pub type SetIterator<T> = HashTableIterator<T, ()>;

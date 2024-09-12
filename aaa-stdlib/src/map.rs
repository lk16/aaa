use std::{
    cell::RefCell,
    collections::HashMap,
    fmt::{Display, Formatter, Result},
    hash::{Hash, Hasher},
    rc::Rc,
};

use crate::var::UserType;

pub struct Map<K, V>
where
    K: UserType,
    V: UserType,
{
    inner: HashMap<K, V>,
    iterator_count: Rc<RefCell<usize>>,
}

impl<K, V> Map<K, V>
where
    K: UserType,
    V: UserType,
{
    pub fn new() -> Self {
        Self {
            inner: HashMap::new(),
            iterator_count: Rc::new(RefCell::new(0)),
        }
    }

    pub fn get(&self, key: &K) -> Option<V> {
        self.inner.get(key).cloned()
    }

    pub fn contains_key(&self, key: &K) -> bool {
        self.get(key).is_some()
    }

    pub fn insert(&mut self, key: K, value: V) {
        self.detect_invalid_change();
        self.inner.insert(key, value);
    }

    pub fn len(&self) -> usize {
        self.inner.len()
    }

    pub fn is_empty(&self) -> bool {
        self.inner.is_empty()
    }

    pub fn clear(&mut self) {
        self.detect_invalid_change();
        self.inner.clear();
    }

    pub fn remove_entry(&mut self, key: &K) -> Option<(K, V)> {
        self.detect_invalid_change();
        self.inner.remove_entry(key)
    }

    pub fn iter(&self) -> MapIterator<K, V> {
        MapIterator::new(self.inner.clone().into_iter(), self.iterator_count.clone())
    }

    fn detect_invalid_change(&self) {
        if *self.iterator_count.borrow() != 0 {
            panic!(
                "HashTable does not allow changes! This probably means it is being iterated over."
            );
        }
    }

    pub fn fmt_as_set(&self) -> String {
        let mut parts = vec![];
        for (item, _) in self.iter() {
            parts.push(format!("{item:?}"));
        }
        format!("{{{}}}", parts.join(","))
    }
}

impl<K, V> PartialEq for Map<K, V>
where
    K: UserType,
    V: UserType,
{
    fn eq(&self, other: &Self) -> bool {
        return self.inner == other.inner;
    }
}

impl<K, V> Eq for Map<K, V>
where
    K: UserType,
    V: UserType,
{
}

impl<K, V> Display for Map<K, V>
where
    K: UserType,
    V: UserType,
{
    fn fmt(&self, f: &mut Formatter<'_>) -> Result {
        let mut parts = vec![];
        for (k, v) in self.iter() {
            parts.push(format!("{k:?}: {v:?}"));
        }
        write!(f, "{{{}}}", parts.join(", "))
    }
}

impl<K, V> Clone for Map<K, V>
where
    K: UserType,
    V: UserType,
{
    fn clone(&self) -> Self {
        let mut map = Map::new();
        for (key, value) in self.iter() {
            map.insert(key, value);
        }

        map
    }
}

impl<K, V> Hash for Map<K, V>
where
    K: UserType,
    V: UserType,
{
    fn hash<H: Hasher>(&self, _state: &mut H) {
        unreachable!() // Won't be implemented
    }
}

impl<K, V> Default for Map<K, V>
where
    K: UserType,
    V: UserType,
{
    fn default() -> Self {
        Self::new()
    }
}

pub struct MapIterator<K, V>
where
    K: UserType,
    V: UserType,
{
    iterator: std::collections::hash_map::IntoIter<K, V>,
    iterator_count: Rc<RefCell<usize>>,
}

impl<K, V> MapIterator<K, V>
where
    K: UserType,
    V: UserType,
{
    pub fn new(
        iterator: std::collections::hash_map::IntoIter<K, V>,
        iterator_count: Rc<RefCell<usize>>,
    ) -> Self {
        *iterator_count.borrow_mut() += 1;

        Self {
            iterator,
            iterator_count,
        }
    }
}

impl<K, V> Iterator for MapIterator<K, V>
where
    K: UserType,
    V: UserType,
{
    type Item = (K, V);

    fn next(&mut self) -> Option<Self::Item> {
        self.iterator.next()
    }
}

impl<K, V> Drop for MapIterator<K, V>
where
    K: UserType,
    V: UserType,
{
    fn drop(&mut self) {
        *self.iterator_count.borrow_mut() -= 1;
    }
}

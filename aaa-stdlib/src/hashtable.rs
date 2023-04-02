use std::{
    cell::RefCell,
    collections::hash_map::DefaultHasher,
    hash::{Hash, Hasher},
    rc::Rc,
};

pub struct HashTable<K, V>
where
    K: Clone + PartialEq + Hash,
    V: Clone + PartialEq,
{
    buckets: Rc<RefCell<Vec<Vec<(K, V)>>>>,
    size: usize,
    iterator_count: Rc<RefCell<usize>>,
}

impl<K, V> HashTable<K, V>
where
    K: Clone + PartialEq + Hash,
    V: Clone + PartialEq,
{
    pub fn new() -> Self {
        Self {
            buckets: Rc::new(RefCell::new(vec![vec![]; 16])),
            size: 0,
            iterator_count: Rc::new(RefCell::new(0)),
        }
    }

    fn get_bucket_id(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        let hash = hasher.finish();
        hash as usize % self.buckets.borrow().len()
    }

    fn find_in_bucket(&self, bucket_id: usize, key: &K) -> Option<V> {
        let bucket = &self.buckets.borrow()[bucket_id];

        for (k, v) in bucket.iter() {
            if key == k {
                return Some(v.clone());
            }
        }
        None
    }

    pub fn get(&self, key: &K) -> Option<V> {
        let bucket_id = self.get_bucket_id(key);
        self.find_in_bucket(bucket_id, key)
    }

    pub fn contains_key(&self, key: &K) -> bool {
        self.get(key).is_some()
    }

    pub fn insert(&mut self, key: K, value: V) {
        self.detect_invalid_change();

        let bucket_id = self.get_bucket_id(&key);
        let bucket = &mut self.buckets.borrow_mut()[bucket_id];

        for (k, v) in bucket.iter_mut() {
            if key == *k {
                *v = value;
                return;
            }
        }

        bucket.push((key, value));
        self.size += 1;

        // TODO maybe rehash
    }

    pub fn rehash(&mut self) {
        self.detect_invalid_change();
        todo!();
    }

    pub fn len(&self) -> usize {
        self.size
    }

    pub fn is_empty(&self) -> bool {
        self.size == 0
    }

    pub fn clear(&mut self) {
        self.detect_invalid_change();

        for bucket in self.buckets.borrow_mut().iter_mut() {
            bucket.clear();
        }
        self.size = 0;
    }

    pub fn remove_entry(&mut self, key: &K) -> Option<(K, V)> {
        self.detect_invalid_change();

        let bucket_id = self.get_bucket_id(&key);
        let bucket = &mut self.buckets.borrow_mut()[bucket_id];

        let position = bucket.iter().position(|(k, _v)| k == key);

        match position {
            Some(index) => {
                self.size -= 1;
                Some(bucket.remove(index))
            }
            None => None,
        }
    }

    pub fn iter(&self) -> HashTableIterator<K, V> {
        HashTableIterator::new(self.buckets.clone(), self.iterator_count.clone())
    }

    fn detect_invalid_change(&self) {
        if *self.iterator_count.borrow() != 0 {
            panic!(
                "HashTable does not allow changes! This probably means it is being iterated over."
            );
        }
    }
}

impl<K, V> PartialEq for HashTable<K, V>
where
    K: Clone + PartialEq + Hash,
    V: Clone + PartialEq,
{
    fn eq(&self, other: &Self) -> bool {
        if self.len() != other.len() {
            return false;
        }

        for (key, value) in self.iter() {
            match other.get(&key) {
                None => return false,
                Some(v) => {
                    if v != value {
                        return false;
                    }
                }
            }
        }

        true
    }
}

pub struct HashTableIterator<K, V>
where
    K: Clone + PartialEq + Hash,
    V: Clone + PartialEq,
{
    buckets: Rc<RefCell<Vec<Vec<(K, V)>>>>,
    iterator_count: Rc<RefCell<usize>>,
    bucket_id: usize,
    offset_in_bucket: usize,
}

impl<K, V> HashTableIterator<K, V>
where
    K: Clone + PartialEq + Hash,
    V: Clone + PartialEq,
{
    pub fn new(buckets: Rc<RefCell<Vec<Vec<(K, V)>>>>, iterator_count: Rc<RefCell<usize>>) -> Self {
        *iterator_count.borrow_mut() += 1;

        Self {
            buckets,
            iterator_count,
            bucket_id: 0,
            offset_in_bucket: 0,
        }
    }
}

impl<K, V> Iterator for HashTableIterator<K, V>
where
    K: Clone + PartialEq + Hash,
    V: Clone + PartialEq,
{
    type Item = (K, V);

    fn next(&mut self) -> Option<Self::Item> {
        let buckets = self.buckets.borrow();

        loop {
            match buckets.get(self.bucket_id) {
                Some(bucket) => match bucket.get(self.offset_in_bucket) {
                    Some((k, v)) => {
                        self.offset_in_bucket += 1;
                        return Some((k.clone(), v.clone()));
                    }
                    None => {
                        self.bucket_id += 1;
                        self.offset_in_bucket = 0;
                    }
                },
                None => return None,
            }
        }
    }
}

impl<K, V> Drop for HashTableIterator<K, V>
where
    K: Clone + PartialEq + Hash,
    V: Clone + PartialEq,
{
    fn drop(&mut self) {
        *self.iterator_count.borrow_mut() -= 1;
    }
}

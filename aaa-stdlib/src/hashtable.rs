use std::{
    collections::hash_map::DefaultHasher,
    hash::{Hash, Hasher},
};

pub struct HashTable<K, V> {
    buckets: Vec<Vec<(K, V)>>,
    size: usize,
}

impl<K, V> HashTable<K, V>
where
    K: Hash + PartialEq,
    V: Clone + PartialEq,
{
    pub fn new() -> Self {
        Self {
            buckets: vec![], // TODO put 16x None here
            size: 0,
        }
    }

    fn get_bucket_id(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        let hash = hasher.finish();
        hash as usize % self.buckets.len()
    }

    fn find_in_bucket(&self, bucket_id: usize, key: &K) -> Option<V> {
        let bucket = &self.buckets[bucket_id];

        for (k, v) in bucket.iter() {
            if key == k {
                return Some(v.clone());
            }
        }
        None
    }

    fn find_in_bucket_mut(&mut self, bucket_id: usize, key: &K) -> Option<&mut V> {
        let bucket = &mut self.buckets[bucket_id];

        for (k, v) in bucket.iter_mut() {
            if key == k {
                return Some(v);
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
        let bucket_id = self.get_bucket_id(&key);

        let found = self.find_in_bucket_mut(bucket_id, &key);

        match found {
            Some(v) => *v = value,
            None => {
                self.buckets[bucket_id].push((key, value));
                self.size += 1;
                self.rehash();
            }
        }
    }

    pub fn rehash(&mut self) {
        todo!();
    }

    pub fn len(&self) -> usize {
        self.size
    }

    pub fn is_empty(&self) -> bool {
        self.size == 0
    }

    pub fn clear(&mut self) {
        todo!();
    }

    pub fn remove_entry(&mut self, key: &K) -> Option<(K, V)> {
        todo!();
    }

    pub fn iter(&self) -> HashTableIterator<K, V> {
        todo!();
    }
}

impl<K, V> PartialEq for HashTable<K, V>
where
    K: Hash + PartialEq,
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
    K: Hash + PartialEq,
    V: Clone + PartialEq,
{
    dummy: (K, V), // TODO remove
}

impl<K, V> Iterator for HashTableIterator<K, V>
where
    K: Hash + PartialEq,
    V: Clone + PartialEq,
{
    type Item = (K, V);

    fn next(&mut self) -> Option<Self::Item> {
        todo!();
    }
}

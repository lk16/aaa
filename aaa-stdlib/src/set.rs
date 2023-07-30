use std::{
    fmt::{Display, Formatter, Result},
    hash::Hash,
};

use crate::{
    map::{HashTableIterator, Map},
    var::UserType,
};

// Can't use unit type `()` as it does not implement Display, Hash or UserType
#[derive(Clone, Debug, Hash, PartialEq)]
pub struct SetValue;

impl Display for SetValue {
    fn fmt(&self, _f: &mut Formatter<'_>) -> Result {
        Ok(())
    }
}

impl UserType for SetValue {
    fn kind(&self) -> String {
        String::from("SetValue")
    }

    fn clone_recursive(&self) -> Self {
        Self {}
    }
}

pub type Set<T> = Map<T, SetValue>;

pub type SetIterator<T> = HashTableIterator<T, SetValue>;

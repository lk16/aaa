use std::path::PathBuf;

use sha2::{Digest, Sha256};

use super::position::Position;

pub fn hash_key(key_tuple: (PathBuf, String)) -> String {
    let mut hasher = Sha256::new();
    hasher.update(key_tuple.0.to_string_lossy().as_bytes());
    hasher.update(key_tuple.1.as_bytes());

    let hash = hasher.finalize();
    let hash = format!("{:x}", hash);

    hash[..16].to_owned()
}

pub fn hash_position(position: &Position) -> String {
    let mut hasher = Sha256::new();
    hasher.update(format!("{}", position).as_bytes());

    let hash = hasher.finalize();
    let hash = format!("{:x}", hash);

    hash[..16].to_owned()
}

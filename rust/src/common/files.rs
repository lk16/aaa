use std::path::Component;
use std::path::{Path, PathBuf};

use rand::Rng;

pub fn repository_root() -> PathBuf {
    Path::new(file!())
        .canonicalize()
        .unwrap()
        .ancestors()
        .skip(4)
        .next()
        .unwrap()
        .to_path_buf()
}

pub fn normalize_path(path: &PathBuf, current_dir: &PathBuf) -> PathBuf {
    let path = if path.is_relative() {
        current_dir.join(&path)
    } else {
        path.clone()
    };

    let mut normalized_path = PathBuf::new();

    for component in path.components() {
        match component {
            Component::CurDir => (),
            Component::ParentDir => {
                normalized_path.pop();
            }
            _ => normalized_path.push(component.as_os_str()),
        }
    }

    normalized_path
}

pub fn random_folder_name() -> String {
    rand::thread_rng()
        .sample_iter(rand::distributions::Alphanumeric)
        .take(10)
        .map(char::from)
        .collect()
}

#[cfg(test)]
pub fn find_aaa_files() -> Vec<PathBuf> {
    let root = repository_root();
    let mut files = Vec::new();
    visit_dirs(root.as_ref(), "aaa", &mut files).unwrap();
    files
}

#[cfg(test)]
fn visit_dirs(dir: &Path, extension: &str, files: &mut Vec<PathBuf>) -> std::io::Result<()> {
    if dir.is_dir() {
        for entry in dir.read_dir()? {
            let entry = entry?;
            let path = entry.path();
            if path.is_dir() {
                visit_dirs(&path, extension, files)?;
            } else {
                if let Some(ext) = path.extension() {
                    if ext == extension {
                        files.push(path);
                    }
                }
            }
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use std::path::PathBuf;

    use rstest::rstest;

    use super::normalize_path;

    #[rstest]
    #[case("/foo/bar", "/home/user/aaa", "/foo/bar")]
    #[case("/foo/./bar", "/home/user/aaa", "/foo/bar")]
    #[case("/foo/../bar", "/home/user/aaa", "/bar")]
    #[case("foo/bar", "/home/user/aaa", "/home/user/aaa/foo/bar")]
    #[case("foo/./bar", "/home/user/aaa", "/home/user/aaa/foo/bar")]
    #[case("foo/../bar", "/home/user/aaa", "/home/user/aaa/bar")]
    fn test_normalize_path(#[case] path: &str, #[case] current_dir: &str, #[case] expected: &str) {
        let path = PathBuf::from(path);
        let current_dir = PathBuf::from(current_dir);
        let normalized = normalize_path(&path, &current_dir);

        assert_eq!(normalized.to_str().unwrap(), expected);
    }
}

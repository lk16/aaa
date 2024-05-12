#[cfg(test)]
use std::path::{Path, PathBuf};

#[cfg(test)]
pub fn get_repository_root() -> PathBuf {
    Path::new(file!())
        .canonicalize()
        .unwrap()
        .ancestors()
        .skip(4)
        .next()
        .unwrap()
        .to_path_buf()
}

#[cfg(test)]
pub fn find_aaa_files() -> Vec<PathBuf> {
    let root = get_repository_root();
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

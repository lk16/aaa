use std::{fmt, path::PathBuf};

#[derive(Debug, Clone, Default, PartialEq, Eq, PartialOrd, Ord)]
pub struct Position {
    pub path: PathBuf,
    pub line: usize,
    pub column: usize,
}

impl Position {
    pub fn new<P: Into<PathBuf>>(path: P, line: usize, column: usize) -> Self {
        Position {
            path: path.into(),
            line,
            column,
        }
    }

    pub fn after(&self, string: &String) -> Self {
        let newline_indices: Vec<_> = string
            .match_indices("\n")
            .into_iter()
            .map(|(n, _)| n)
            .collect();

        let line = self.line + newline_indices.len();

        let column = match newline_indices.last() {
            None => self.column + string.len(),
            Some(offset) => string.len() - offset,
        };

        Position::new(self.path.clone(), line, column)
    }
}

impl fmt::Display for Position {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.path.to_str().unwrap();
        write!(
            f,
            "{}:{}:{}",
            self.path.to_str().unwrap(),
            self.line,
            self.column
        )
    }
}

use super::token::Token;
use std::fmt;

#[derive(Debug, Clone)]
pub struct Position {
    file: String,
    line: usize,
    column: usize,
}

impl Position {
    pub fn new(file: String, line: usize, column: usize) -> Self {
        Position { file, line, column }
    }

    pub fn after(&self, token: &Token) -> Self {
        let newline_indices: Vec<_> = token
            .value
            .match_indices("\n")
            .into_iter()
            .map(|(n, _)| n)
            .collect();

        let line = self.line + newline_indices.len();

        let column = match newline_indices.last() {
            None => self.column + token.len(),
            Some(offset) => token.len() - offset,
        };

        Position::new(self.file.clone(), line, column)
    }
}

impl fmt::Display for Position {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}:{}:{}", self.file, self.line, self.column)
    }
}

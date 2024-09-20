use std::{
    fmt::{Debug, Display},
    path::PathBuf,
};

use regex::{Captures, Regex};

use crate::common::position::Position;

use super::types::{Token, TokenType, ENUM_REGEX_PAIRS};

pub struct TokenizerError {
    pub position: Position,
}

impl Debug for TokenizerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Tokenizer error at: {}", self.position)
    }
}

impl Display for TokenizerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}

impl TokenizerError {
    fn new(position: Position) -> Self {
        TokenizerError { position }
    }
}

pub fn tokenize(code: &str, path: Option<PathBuf>) -> Result<Vec<Token>, TokenizerError> {
    let path = path.or(Some(PathBuf::from("/unknown/path.aaa"))).unwrap();

    let mut tokens = vec![];
    let mut position = Position::new(path.clone(), 1, 1);

    for line in code.split_inclusive('\n') {
        let mut offset = 0;
        while offset < line.len() {
            match get_token(line, offset) {
                Some((type_, value)) => {
                    let token = Token::new(type_, value, position.clone());
                    offset += token.len();
                    position = position.after(&token.value);
                    tokens.push(token);
                }
                None => {
                    return Err(TokenizerError::new(position));
                }
            }
        }
    }

    Ok(tokens)
}

pub fn tokenize_filtered(code: &str, path: Option<PathBuf>) -> Result<Vec<Token>, TokenizerError> {
    match tokenize(code, path) {
        Err(err) => Err(err),
        Ok(tokens) => {
            let tokens = tokens
                .into_iter()
                .filter(|token| !token.type_.is_filtered())
                .collect();
            Ok(tokens)
        }
    }
}

fn captures_at_offset<'a>(s: &'a str, re: &Regex, offset: usize) -> Option<Captures<'a>> {
    if offset >= s.len() {
        return None;
    }

    // Get the substring starting at the offset
    let substring = &s[offset..];

    // Check if the regex matches at the start of the substring and get the captures
    re.captures(substring)
        .filter(|caps| caps.get(0).unwrap().start() == 0)
}

fn get_token(line: &str, offset: usize) -> Option<(TokenType, String)> {
    for (token_type, regex, group) in ENUM_REGEX_PAIRS.iter() {
        if let Some(captures) = captures_at_offset(line, regex, offset) {
            let value = String::from(captures.get(*group).unwrap().as_str());
            return Some((*token_type, value));
        }
    }

    None
}

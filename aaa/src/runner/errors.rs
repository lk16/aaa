use std::{fmt::Display, path::PathBuf};

use crate::{
    cross_referencer::errors::CrossReferencerError, parser::parser::ParseError,
    tokenizer::tokenizer::TokenizerError, type_checker::errors::TypeError,
};

pub enum RunnerError {
    EnvVariables(String),
    IO(std::io::Error),
    Tokenizer(TokenizerError),
    Parser(ParseError),
    CrossReferencer(CrossReferencerError),
    Type(TypeError),
    FileNotFound(PathBuf),
    CompilerError(String),
}

impl From<std::io::Error> for RunnerError {
    fn from(value: std::io::Error) -> Self {
        Self::IO(value)
    }
}

impl From<TokenizerError> for RunnerError {
    fn from(value: TokenizerError) -> Self {
        Self::Tokenizer(value)
    }
}

impl From<ParseError> for RunnerError {
    fn from(value: ParseError) -> Self {
        Self::Parser(value)
    }
}

impl From<CrossReferencerError> for RunnerError {
    fn from(value: CrossReferencerError) -> Self {
        Self::CrossReferencer(value)
    }
}

impl From<TypeError> for RunnerError {
    fn from(value: TypeError) -> Self {
        Self::Type(value)
    }
}

impl Display for RunnerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::EnvVariables(error) => write!(f, "{}", error),
            Self::IO(error) => write!(f, "{}", error),
            Self::Parser(error) => write!(f, "{}", error),
            Self::Tokenizer(error) => write!(f, "{}", error),
            Self::CrossReferencer(error) => write!(f, "{}", error),
            Self::Type(error) => write!(f, "{}", error),
            Self::FileNotFound(path) => writeln!(f, "Could not open {}", path.display()),
            Self::CompilerError(stderr) => write!(f, "{}", stderr),
        }
    }
}

pub fn env_var_error<T>(env_var_name: &str) -> Result<T, RunnerError> {
    let message = format!(
        "Missing or poorly formatted environment variable {}",
        env_var_name
    );
    Err(RunnerError::EnvVariables(message))
}

pub fn compiler_error<T>(stderr: String) -> Result<T, RunnerError> {
    Err(RunnerError::CompilerError(stderr))
}

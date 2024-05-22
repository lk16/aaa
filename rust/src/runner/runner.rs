use std::{
    collections::{HashMap, HashSet},
    env,
    fmt::{Debug, Display},
    fs::read_to_string,
    path::PathBuf,
};

use crate::{
    cross_referencer::cross_referencer::cross_reference,
    parser::{
        parser::{parse, ParseError},
        types::SourceFile,
    },
    tokenizer::tokenizer::{tokenize_filtered, TokenizerError},
};

#[derive(Debug)]
pub enum RunnerError {
    CliArguments(String),
    EnvVariables(String),
    IO(std::io::Error),
    Tokenizer(TokenizerError),
    Parser(ParseError),
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

impl Display for RunnerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RunnerError::CliArguments(error) => write!(f, "{}", error),
            RunnerError::EnvVariables(error) => write!(f, "{}", error),
            RunnerError::IO(error) => write!(f, "{}", error),
            RunnerError::Parser(error) => write!(f, "{}", error),
            RunnerError::Tokenizer(error) => write!(f, "{}", error),
        }
    }
}

pub struct Runner {
    entrypoint_path: PathBuf,
    entrypoint_code: String,
    builtins_path: PathBuf,
    current_dir: PathBuf,
}

impl Runner {
    pub fn new(args: Vec<String>) -> Result<Self, RunnerError> {
        if args.len() != 2 {
            return Err(RunnerError::CliArguments(format!(
                "Usage: {} <code_or_file_name>",
                args[0]
            )));
        }

        let current_dir = env::current_dir()?;

        let builtins_path = match env::var("AAA_STDLIB_PATH") {
            Ok(path_string) => PathBuf::from(path_string).join("builtins.aaa"),
            Err(_) => {
                return Err(RunnerError::EnvVariables(format!(
                    "Missing or poorly formatted environment variable AAA_STDLIB_PATH",
                )));
            }
        };

        let runner = if args[1].ends_with(".aaa") {
            let path = PathBuf::from(&args[1]);
            Self {
                entrypoint_code: read_to_string(&path)?,
                entrypoint_path: path,
                builtins_path,
                current_dir,
            }
        } else {
            Self {
                entrypoint_code: args[1].clone(),
                entrypoint_path: PathBuf::from("/dev/stdin"),
                builtins_path,
                current_dir,
            }
        };

        Ok(runner)
    }

    fn parse_entrypoint(&self) -> Result<SourceFile, RunnerError> {
        let parsed = self.parse_file(&self.entrypoint_code, &self.entrypoint_path)?;
        Ok(parsed)
    }

    fn parse_file(&self, code: &String, path: &PathBuf) -> Result<SourceFile, RunnerError> {
        let tokens = tokenize_filtered(&code, Some(path.clone()))?;
        let parsed = parse(tokens)?;

        Ok(parsed)
    }

    fn parse_files(&self) -> Result<HashMap<PathBuf, SourceFile>, RunnerError> {
        let mut parsed_files = HashMap::new();
        let parsed_file = self.parse_entrypoint()?;
        let mut remaining_files = parsed_file
            .dependencies(&self.current_dir)
            .into_iter()
            .collect::<HashSet<_>>();
        let path = self.entrypoint_path.clone();
        parsed_files.insert(path, parsed_file);

        remaining_files.insert(self.builtins_path.clone());

        loop {
            let file = match remaining_files.iter().next() {
                None => break,
                Some(file) => file.clone(),
            };

            remaining_files.remove(&file);

            let code = read_to_string(&file)?;
            let parsed_file = self.parse_file(&code, &file)?;

            for dependency in parsed_file.dependencies(&self.current_dir) {
                if !parsed_files.contains_key(&dependency) {
                    remaining_files.insert(dependency);
                }
            }

            parsed_files.insert(file, parsed_file);
        }

        Ok(parsed_files)
    }

    pub fn run(&self) -> i32 {
        let parsed_files = match self.parse_files() {
            Ok(parsed_files) => parsed_files,
            Err(error) => {
                eprintln!("{:?}", error);
                return 1;
            }
        };

        let _ = match cross_reference(
            parsed_files,
            self.entrypoint_path.clone(),
            self.builtins_path.clone(),
            self.current_dir.clone(),
        ) {
            Ok(cross_referenced) => cross_referenced,
            Err(errors) => {
                for error in &errors {
                    eprintln!("{:?}", error);
                }

                eprintln!("Found {} errors", errors.len());
                return 1;
            }
        };

        0
    }
}

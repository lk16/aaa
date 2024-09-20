use std::{
    collections::{HashMap, HashSet},
    env,
    fs::{self, read_to_string},
    io,
    path::PathBuf,
    process::Command,
};

use crate::{
    common::files::{random_folder_name, repository_root},
    cross_referencer::cross_referencer::cross_reference,
    parser::{parser::parse, types::SourceFile},
    tokenizer::tokenizer::tokenize_filtered,
    transpiler::transpiler::Transpiler,
    type_checker::type_checker::type_check,
};

use super::errors::{cli_arg_error, compiler_error, env_var_error, RunnerError};

pub struct Runner {
    entrypoint_path: PathBuf,
    entrypoint_code: String,
    builtins_path: PathBuf,
    current_dir: PathBuf,
}

impl Runner {
    pub fn new(args: Vec<String>) -> Result<Self, RunnerError> {
        if args.len() != 2 {
            return cli_arg_error(&args[0]);
        }

        let current_dir = env::current_dir()?;

        let builtins_path = match env::var("AAA_STDLIB_PATH") {
            Ok(path_string) => PathBuf::from(path_string).join("builtins.aaa"),
            Err(_) => return env_var_error("AAA_STDLIB_PATH"),
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

            let code = match read_to_string(&file) {
                Err(error) => match error.kind() {
                    io::ErrorKind::NotFound => return Err(RunnerError::FileNotFound(file)),
                    _ => return Err(RunnerError::IO(error)),
                },
                Ok(code) => code,
            };

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

    fn get_transpiler_root_path() -> PathBuf {
        env::temp_dir()
            .join("aaa-transpiled")
            .join(random_folder_name())
    }

    fn compile(&self, transpiler_root_path: &PathBuf) -> Result<PathBuf, RunnerError> {
        // Use shared target dir between executables,
        // because every Aaa compilation would otherwise take 120 MB disk,
        // due to Rust dependencies.

        let cargo_target_dir = env::temp_dir().join("aaa-shared-target");

        fs::create_dir_all(&cargo_target_dir).unwrap();

        let cargo_toml = transpiler_root_path.join("Cargo.toml");
        let stdlib_impl_path = repository_root().join("aaa-stdlib");

        // Join strings in this ugly fashion to prevent leading whitespace in generated Cargo.toml
        let cargo_toml_content = vec![
            "[package]",
            "name = \"aaa-stdlib-user\"",
            "version = \"0.1.0\"",
            "edition = \"2021\"",
            "",
            "[dependencies]",
            format!(
                "aaa-stdlib = {{ version = \"0.1.0\", path = \"{}\" }}",
                stdlib_impl_path.display()
            )
            .as_str(),
            "regex = \"1.8.4\"",
            "",
        ]
        .join("\n");

        fs::write(&cargo_toml, cargo_toml_content).unwrap();

        let cargo_toml = format!("{}", cargo_toml.display());

        let output = Command::new("cargo")
            .args([
                "build",
                "--release",
                "--quiet",
                "--color",
                "always",
                "--manifest-path",
                cargo_toml.as_str(),
            ])
            .env("CARGO_TARGET_DIR", cargo_target_dir.as_os_str())
            .output()
            .unwrap();

        // TODO #215 use CLI args here instead of env var
        if env::var("AAA_DEBUG").is_ok() {
            let status = output.status.code().unwrap();

            if status != 0 {
                let stderr = String::from_utf8_lossy(&output.stderr).to_string();
                return compiler_error(stderr);
            }
        }

        Ok(cargo_target_dir.join("release/aaa-stdlib-user"))
    }

    pub fn run(&self) -> i32 {
        let parsed_files = match self.parse_files() {
            Ok(parsed_files) => parsed_files,
            Err(error) => {
                eprintln!("{}", error);
                return 1;
            }
        };

        let cross_referenced = match cross_reference(
            parsed_files,
            self.entrypoint_path.clone(),
            self.builtins_path.clone(),
            self.current_dir.clone(),
        ) {
            Ok(cross_referenced) => cross_referenced,
            Err(errors) => {
                for error in &errors {
                    eprint!("{}", error);
                }
                eprintln!("");
                eprintln!("Found {} errors", errors.len());
                return 1;
            }
        };

        let type_checked = match type_check(cross_referenced.clone()) {
            Err(type_errors) => {
                for error in &type_errors {
                    eprint!("{}", error);
                }
                eprintln!("");
                eprintln!("Found {} errors", type_errors.len());
                return 1;
            }
            Ok(type_checked) => type_checked,
        };

        let transpiler_root_path = Self::get_transpiler_root_path();
        let transpiler = Transpiler::new(transpiler_root_path.clone(), type_checked);

        transpiler.run();

        // TODO #215 make compilation optional
        let binary_path = match self.compile(&transpiler_root_path) {
            Ok(binary_path) => binary_path,
            Err(error) => {
                eprintln!("{}", error);
                return 1;
            }
        };

        // TODO #215 make executing binary optional
        // TODO #215 handle errors better and forward exit code
        Command::new(binary_path).spawn().unwrap();

        0
    }
}

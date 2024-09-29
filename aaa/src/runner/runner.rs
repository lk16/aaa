use std::{
    collections::{HashMap, HashSet},
    env,
    fs::{self, read_to_string},
    io,
    path::{Path, PathBuf},
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

use super::errors::{compiler_error, env_var_error, RunnerError};

#[derive(Default)]
pub struct RunnerOptions {
    pub file: String,
    pub output_binary: Option<PathBuf>,
    pub verbose: bool,
    pub command: String,
}

pub struct Runner {
    entrypoint_path: PathBuf,
    entrypoint_code: String,
    builtins_path: PathBuf,
    current_dir: PathBuf,
    options: RunnerOptions,
}

impl Runner {
    pub fn run_with_options(options: RunnerOptions) -> i32 {
        let runner = match Runner::new(options) {
            Ok(runner) => runner,
            Err(error) => return Self::fail_with_error(error),
        };

        runner.run()
    }

    fn new(options: RunnerOptions) -> Result<Self, RunnerError> {
        let current_dir = env::current_dir()?;

        let builtins_path = match env::var("AAA_STDLIB_PATH") {
            Ok(path_string) => PathBuf::from(path_string).join("builtins.aaa"),
            Err(_) => return env_var_error("AAA_STDLIB_PATH"),
        };

        let runner = if options.file.ends_with(".aaa") {
            let path = PathBuf::from(options.file.clone());
            Self {
                entrypoint_code: read_to_string(&path)?,
                entrypoint_path: path,
                builtins_path,
                current_dir,
                options,
            }
        } else {
            Self {
                entrypoint_code: options.file.clone(),
                entrypoint_path: PathBuf::from("/dev/stdin"),
                builtins_path,
                current_dir,
                options,
            }
        };

        Ok(runner)
    }

    fn should_compile(&self) -> bool {
        self.options.command != "check"
    }

    fn should_run_binary(&self) -> bool {
        self.options.command == "run"
    }

    fn fail_with_error<T: Into<RunnerError>>(error: T) -> i32 {
        Self::fail_with_errors(vec![error])
    }

    fn fail_with_errors<T: Into<RunnerError>>(errors: Vec<T>) -> i32 {
        let error_count = errors.len();

        for error in errors {
            let runner_error: RunnerError = error.into();
            eprint!("{}", runner_error);
        }
        eprintln!();
        eprintln!("Found {} errors", error_count);

        1
    }

    fn parse_entrypoint(&self) -> Result<SourceFile, RunnerError> {
        let parsed = self.parse_file(&self.entrypoint_code, &self.entrypoint_path)?;
        Ok(parsed)
    }

    fn parse_file(&self, code: &str, path: &Path) -> Result<SourceFile, RunnerError> {
        let tokens = tokenize_filtered(code, Some(path.to_path_buf()))?;
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

    fn compile(&self, transpiler_root_path: &Path) -> Result<PathBuf, RunnerError> {
        // Use shared target dir between executables,
        // because every Aaa compilation would otherwise take 120 MB disk,
        // due to Rust dependencies.

        let cargo_target_dir = env::temp_dir().join("aaa-shared-target");

        fs::create_dir_all(&cargo_target_dir).unwrap();

        let cargo_toml = transpiler_root_path.join("Cargo.toml");
        let stdlib_impl_path = repository_root().join("aaa-stdlib");

        // Join strings in this ugly fashion to prevent leading whitespace in generated Cargo.toml
        let cargo_toml_content = [
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

        let status = output.status.code().unwrap();

        if status != 0 {
            let stderr = String::from_utf8_lossy(&output.stderr).to_string();
            return compiler_error(stderr);
        }

        let binary_path = cargo_target_dir.join("release/aaa-stdlib-user");

        if let Some(requested_binary_path) = &self.options.output_binary {
            fs::rename(binary_path, requested_binary_path).unwrap();

            return Ok(requested_binary_path.clone());
        }

        Ok(binary_path)
    }

    fn run(&self) -> i32 {
        let parsed_files = match self.parse_files() {
            Ok(parsed_files) => parsed_files,
            Err(error) => return Self::fail_with_error(error),
        };

        let cross_referenced = match cross_reference(
            parsed_files,
            self.entrypoint_path.clone(),
            self.builtins_path.clone(),
            self.current_dir.clone(),
        ) {
            Ok(cross_referenced) => cross_referenced,
            Err(errors) => return Self::fail_with_errors(errors),
        };

        let type_checked = match type_check(cross_referenced, self.options.verbose) {
            Err(errors) => return Self::fail_with_errors(errors),
            Ok(type_checked) => type_checked,
        };

        let transpiler_root_path = Self::get_transpiler_root_path();
        let transpiler = Transpiler::new(
            transpiler_root_path.clone(),
            type_checked,
            self.options.verbose,
        );

        transpiler.run();

        if self.should_compile() {
            let binary_path = match self.compile(&transpiler_root_path) {
                Ok(binary_path) => binary_path,
                Err(error) => return Self::fail_with_error(error),
            };

            if self.should_run_binary() {
                return Command::new(binary_path)
                    .status()
                    .expect("could not run binary")
                    .code()
                    .unwrap();
            } else if self.options.output_binary.is_none() {
                println!("Generated binary in {}", binary_path.display());
            }
        }

        0
    }
}

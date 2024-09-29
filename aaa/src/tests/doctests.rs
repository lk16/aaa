use std::{
    collections::{BTreeMap, HashMap},
    env,
    fmt::Display,
    fs::{self, read_to_string},
    path::PathBuf,
    process::Command,
};

use crate::common::files::random_folder_name;

enum CommentMode {
    Default,
    Stdout,
    Stderr,
}

#[derive(Default, Clone, Debug)]
struct DocTest {
    name: String,
    path: PathBuf,
    code: HashMap<String, String>,
    expected_status_code: i32,
    expected_stdout: String,
    expected_stderr: String,
    source_path: PathBuf,
    skipped: bool,
}

impl DocTest {
    fn pretty_name(&self) -> String {
        let cur_dir = format!("{}", env::current_dir().unwrap().display());
        let mut path = format!("{}", self.path.display());

        if let Some(relative_path) = path.strip_prefix((cur_dir + "/").as_str()) {
            path = relative_path.to_owned();
        }

        let name = self.name.replace(" ", "-");

        format!("{}::{}", path, name)
    }
}

enum DocTestResult {
    Ok,
    Skipped,
    Err(DocTestError),
}

enum DocTestError {
    Status {
        test_name: String,
        expected: i32,
        found: i32,
    },
    Stdout {
        test_name: String,
        expected: String,
        found: String,
    },
    Stderr {
        test_name: String,
        expected: String,
        found: String,
    },
}

impl Display for DocTestError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Status {
                test_name,
                expected,
                found,
            } => {
                writeln!(f, "Unexpected exit code for \"{}\"", test_name)?;
                writeln!(f, "expected: {}", expected)?;
                writeln!(f, "   found: {}", found)
            }
            Self::Stdout {
                test_name,
                expected,
                found,
            } => {
                writeln!(f, "Unexpected stdout for \"{}\"", test_name)?;
                writeln!(f, "expected:\n{}", expected)?;
                writeln!(f, "found:\n{}", found)
            }
            Self::Stderr {
                test_name,
                expected,
                found,
            } => {
                writeln!(f, "Unexpected stderr for \"{}\"", test_name)?;
                writeln!(f, "expected:\n{}", expected)?;
                writeln!(f, "found:\n{}", found)
            }
        }
    }
}

pub struct DocTestRunner {
    paths: Vec<PathBuf>,

    // Use BTree so tests run in same order every time
    doc_tests: BTreeMap<(PathBuf, String), DocTest>,
    stdlib_path: String,
    filter: Option<String>,
}

impl DocTestRunner {
    pub fn new() -> Self {
        let cur_dir = env::current_dir().unwrap();
        let doctest_base_path = cur_dir.join("src/tests/src");

        let mut paths = vec![];

        for entry in doctest_base_path.read_dir().unwrap() {
            let path = entry.unwrap().path();
            paths.push(path);
        }

        Self {
            paths,
            doc_tests: BTreeMap::default(),
            stdlib_path: std::env::var("AAA_STDLIB_PATH").unwrap(),
            filter: None,
        }
    }

    pub fn set_filter(&mut self, test_or_file: &str) {
        self.filter = Some(test_or_file.to_owned());
    }

    fn filter_tests(&mut self) {
        let Some(ref test_or_file) = self.filter else {
            return;
        };

        let test_or_file = test_or_file.as_str();

        let mut filtered_tests = BTreeMap::new();

        for ((path, name), doc_test) in &self.doc_tests {
            let path_str = format!("{}", path.display());

            if path_str.starts_with(test_or_file)
                || doc_test.pretty_name().starts_with(test_or_file)
            {
                filtered_tests.insert((path.clone(), name.clone()), doc_test.clone());
            }
        }

        self.doc_tests = filtered_tests;
    }

    pub fn run(&mut self) -> i32 {
        print!("\n\n");

        for path in self.paths.clone() {
            self.parse_doctest_file(path);
        }

        self.filter_tests();

        let mut skipped_tests = 0;
        let mut errors = vec![];

        for doc_test in self.doc_tests.values() {
            match self.run_doc_test(&doc_test) {
                DocTestResult::Ok => (),
                DocTestResult::Skipped => skipped_tests += 1,
                DocTestResult::Err(error) => errors.push(error),
            }
        }

        for error in &errors {
            println!();
            print!("{}", error);
        }

        let run_tests = self.doc_tests.len() - skipped_tests;
        let failed_tests = errors.len();
        let passed_tests = run_tests - failed_tests;

        println!();
        println!(
            "Ran {} doctests: {} passed, {} skipped, {} failed.",
            run_tests, passed_tests, skipped_tests, failed_tests
        );
        println!();

        if failed_tests != 0 || run_tests == 0 {
            return 1;
        }

        0
    }

    fn parse_doctest_file(&mut self, path: PathBuf) {
        let file_content = read_to_string(&path).expect("could not read file");
        let sections = Self::split_file(file_content);

        for section in sections {
            let doc_test = Self::parse_doc_test(&path, section);

            let key = (path.clone(), doc_test.name.clone());

            if self.doc_tests.insert(key, doc_test.clone()).is_some() {
                panic!(
                    "Found multiple doctests in {:?} with name \"{}\"",
                    path, doc_test.name
                );
            }
        }
    }

    fn split_file(file_content: String) -> Vec<Vec<String>> {
        let mut sections = vec![];
        let mut section = vec![];

        for line in file_content.split_inclusive('\n') {
            if line.starts_with("/// ---") {
                sections.push(section);
                section = vec![];
                continue;
            }

            section.push(line.to_owned());
        }

        sections.push(section);

        sections
    }

    fn parse_doc_test(path: &PathBuf, lines: Vec<String>) -> DocTest {
        use CommentMode::*;

        let mut comment_mode = Default;
        let mut doc_test = DocTest {
            path: path.clone(),
            source_path: env::temp_dir()
                .join("aaa-doctests")
                .join(random_folder_name()),
            ..DocTest::default()
        };

        let mut file_name = "main.aaa".to_owned();

        for line in lines {
            if line == "\n" {
                comment_mode = Default;
                continue;
            }

            if let Some(suffix) = line.strip_prefix("/// skip") {
                // Prevent finding marker with grep
                let to_do = String::from("TO") + "DO";

                if !suffix.contains(&to_do) {
                    panic!(
                        "Found skipped doctest without {} comment on same line",
                        to_do
                    );
                }
                doc_test.skipped = true;
            }

            if let Some(suffix) = line.strip_prefix("/// name:") {
                doc_test.name = suffix.trim().to_owned();
                continue;
            }

            if let Some(suffix) = line.strip_prefix("/// file:") {
                file_name = suffix.trim().to_owned();
                continue;
            }

            if let Some(suffix) = line.strip_prefix("/// status:") {
                doc_test.expected_status_code = suffix
                    .trim()
                    .parse::<i32>()
                    .expect("could not parse status code");
                continue;
            }

            if line.starts_with("/// stdout:") {
                comment_mode = Stdout;
                continue;
            }

            if line.starts_with("/// stderr:") {
                comment_mode = Stderr;
                continue;
            }

            if let Some(suffix) = line.strip_prefix("/// ").or(line.strip_prefix("///")) {
                match comment_mode {
                    Default => (),
                    Stdout => doc_test.expected_stdout.push_str(suffix),
                    Stderr => doc_test.expected_stderr.push_str(suffix),
                }
                continue;
            }

            let code = doc_test.code.entry(file_name.clone()).or_default();

            code.push_str(&line);
            comment_mode = Default;
        }

        doc_test
    }

    fn run_doc_test(&self, doc_test: &DocTest) -> DocTestResult {
        print!("{} ... ", doc_test.pretty_name());

        if doc_test.skipped {
            println!("SKIPPED");
            return DocTestResult::Skipped;
        }

        fs::create_dir_all(&doc_test.source_path).unwrap();

        for (file_name, content) in &doc_test.code {
            fs::write(doc_test.source_path.join(file_name), content).unwrap();
        }

        let source_path = doc_test.source_path.to_string_lossy().into_owned();

        let main_file = doc_test
            .source_path
            .join("main.aaa")
            .to_string_lossy()
            .into_owned();

        // Enable optimizations with `--release` to speed up running doctests.
        let output = Command::new("cargo")
            .args(["run", "-q", "--release", "check", &main_file])
            .output()
            .expect("Failed to execute command");

        let stdout = String::from_utf8_lossy(&output.stdout)
            .replace(&self.stdlib_path, "$AAA_STDLIB_PATH")
            .replace(&source_path, "$SOURCE_PATH");

        let stderr = String::from_utf8_lossy(&output.stderr)
            .replace(&self.stdlib_path, "$AAA_STDLIB_PATH")
            .replace(&source_path, "$SOURCE_PATH");

        let status_code = output.status.code().unwrap();

        if doc_test.expected_stdout != stdout {
            println!("FAIL");

            return DocTestResult::Err(DocTestError::Stdout {
                test_name: doc_test.pretty_name(),
                expected: doc_test.expected_stdout.clone(),
                found: stdout,
            });
        }

        if doc_test.expected_stderr != stderr {
            println!("FAIL");

            return DocTestResult::Err(DocTestError::Stderr {
                test_name: doc_test.pretty_name(),
                expected: doc_test.expected_stderr.clone(),
                found: stderr,
            });
        }

        if doc_test.expected_status_code != status_code {
            println!("FAIL");

            return DocTestResult::Err(DocTestError::Status {
                test_name: doc_test.pretty_name(),
                expected: doc_test.expected_status_code,
                found: status_code,
            });
        }

        println!("OK");
        return DocTestResult::Ok;
    }
}

#[cfg(test)]
mod tests {
    use super::DocTestRunner;

    #[test]
    fn test_doctests() {
        let ok = DocTestRunner::new().run();
        assert_eq!(ok, 0);
    }
}

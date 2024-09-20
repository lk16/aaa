#[cfg(test)]
mod tests {
    use std::{
        collections::{HashMap, HashSet},
        env,
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
        files: HashMap<String, String>,
        expected_status_code: i32,
        expected_stdout: String,
        expected_stderr: String,
        source_path: PathBuf,
        skipped: bool,
    }

    struct DocTestRunner {
        path: PathBuf,
        names: HashSet<String>,
        doc_tests: Vec<DocTest>,
        stdlib_path: String,
    }

    impl DocTestRunner {
        fn new(path: PathBuf) -> Self {
            Self {
                path: path.clone(),
                names: HashSet::default(),
                doc_tests: vec![],
                stdlib_path: std::env::var("AAA_STDLIB_PATH").unwrap(),
            }
        }

        fn run(&mut self) {
            let file_content = read_to_string(self.path.clone()).expect("could not read file");
            let sections = Self::split_file(file_content);

            for section in sections {
                let doc_test = Self::parse_doc_test(section);

                if !self.names.insert(doc_test.name.clone()) {
                    panic!(
                        "Found multiple doctests in {:?} with name \"{}\"",
                        self.path, doc_test.name
                    );
                }

                self.doc_tests.push(doc_test);
            }

            for doc_test in &self.doc_tests {
                self.run_doc_test(&doc_test);
            }

            // TODO #222 Do not crash immediately on failed test and delete self.source_path
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

        fn parse_doc_test(lines: Vec<String>) -> DocTest {
            use CommentMode::*;

            let mut comment_mode = Default;
            let mut doc_test = DocTest::default();

            doc_test.source_path = env::temp_dir()
                .join("aaa-doctests")
                .join(random_folder_name());

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

                let code = doc_test.files.entry(file_name.clone()).or_default();

                code.push_str(&line);
                comment_mode = Default;
            }

            doc_test
        }

        fn run_doc_test(&self, doc_test: &DocTest) {
            if doc_test.skipped {
                println!("Skipping doctest {} ...", doc_test.name);
                return;
            }

            println!("Running doctest {} ...", doc_test.name);

            fs::create_dir_all(&doc_test.source_path).unwrap();

            for (file_name, content) in &doc_test.files {
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
                .args(["run", "-q", "--release", &main_file])
                .output()
                .expect("Failed to execute command");

            assert_eq!(
                doc_test.expected_stdout,
                String::from_utf8_lossy(&output.stdout)
                    .replace(&self.stdlib_path, "$AAA_STDLIB_PATH")
                    .replace(&source_path, "$SOURCE_PATH"),
                "Unexpected stdout for doc test \"{}\"",
                doc_test.name,
            );

            assert_eq!(
                doc_test.expected_stderr,
                String::from_utf8_lossy(&output.stderr)
                    .replace(&self.stdlib_path, "$AAA_STDLIB_PATH")
                    .replace(&source_path, "$SOURCE_PATH"),
                "Unexpected stderr for doc test \"{}\"",
                doc_test.name,
            );

            assert_eq!(
                doc_test.expected_status_code,
                output.status.code().unwrap(),
                "Unexpected exit code for doc test \"{}\"",
                doc_test.name,
            );
        }
    }

    #[test]
    fn test_code() {
        let cur_dir = env::current_dir().unwrap();
        let test_file = cur_dir.join("src/tests/test_code.aaa");

        DocTestRunner::new(test_file).run();
    }
}

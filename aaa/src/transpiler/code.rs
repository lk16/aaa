const INDENTATION: &'static str = "    ";

pub struct Code {
    lines: Vec<String>,
    indent_level: usize,
}

impl Code {
    pub fn new() -> Self {
        Self {
            lines: vec![],
            indent_level: 0,
        }
    }

    pub fn from_string<T: Into<String>>(string: T) -> Self {
        let mut code = Self::new();
        code.add_line(string);
        code
    }

    pub fn add_line<T: Into<String>>(&mut self, value: T) {
        let string: String = value.into();

        if string.ends_with("\n") {
            panic!("add_line() string should not end with newline!")
        }

        if string.ends_with('}') || string.ends_with("},") {
            if self.indent_level == 0 {
                panic!("Cannot indent below level 0.");
            }

            self.indent_level -= 1;
        }

        let prefix = INDENTATION.repeat(self.indent_level);
        let line = format!("{}{}", prefix, string);

        self.lines.push(line);

        if string.ends_with('{') {
            self.indent_level += 1;
        }
    }

    pub fn add_code(&mut self, code: Code) {
        let prefix = INDENTATION.repeat(self.indent_level);

        for line in &code.lines {
            self.lines.push(format!("{}{}", prefix, line));
        }
    }

    pub fn get(&self) -> String {
        self.lines.join("\n") + "\n"
    }
}

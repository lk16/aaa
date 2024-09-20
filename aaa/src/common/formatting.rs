use std::fmt::Display;

pub fn join_display<T: Display>(separator: &str, values: &Vec<T>) -> String {
    values
        .iter()
        .map(|value| format!("{}", value))
        .collect::<Vec<_>>()
        .join(separator)
}

pub fn join_display_prefixed<T: Display>(prefix: &str, separator: &str, values: &Vec<T>) -> String {
    let suffix = join_display(separator, values);

    format!("{}{}", prefix.to_owned(), suffix)
        .trim_end()
        .to_string()
}

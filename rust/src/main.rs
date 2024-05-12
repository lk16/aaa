use std::env;
use std::fs;

mod parser;

use parser::token_type::TokenType;
use parser::tokenizer::tokenize;

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() != 2 {
        eprintln!("Usage: {} <file_name>", args[0]);
        std::process::exit(1);
    }

    let file_name = &args[1];

    let file_content = match fs::read_to_string(file_name) {
        Ok(content) => content,
        Err(err) => {
            eprintln!("Error reading file: {}", err);
            std::process::exit(1);
        }
    };

    let tokens = match tokenize(&file_content, Some(file_name)) {
        Err(e) => {
            eprintln!("Tokenizer error at: {}", e.position);
            std::process::exit(1);
        }
        Ok(tokens) => tokens,
    };

    for token in tokens.iter() {
        match token.type_ {
            TokenType::Whitespace => continue,
            _ => println!(
                "{:<30} {:>15} {:?}",
                format!("{}", token.position),
                format!("{:?}", token.type_),
                token.value
            ),
        }
    }
}

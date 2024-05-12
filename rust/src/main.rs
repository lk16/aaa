use std::env;
use std::fs;

mod common;
mod parser;

use parser::parser::parse;
use parser::tokenizer::tokenize_filtered;

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

    let tokens = match tokenize_filtered(&file_content, Some(file_name)) {
        Err(e) => {
            eprintln!("{:?}", e);
            std::process::exit(1);
        }
        Ok(tokens) => tokens,
    };

    for token in tokens.iter() {
        if token.type_.is_filtered() {
            continue;
        }

        println!(
            "{:<50} {:>15} {:?}",
            format!("{}", token.position),
            format!("{:?}", token.type_),
            token.value
        );
    }

    match parse(tokens) {
        Ok(_) => (),
        Err(e) => eprintln!("{}", e),
    }
    // TODO print result
}

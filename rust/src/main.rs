use std::{env, process::exit};

mod common;
mod cross_referencer;
mod parser;
mod runner;
mod tests;
mod tokenizer;
mod type_checker;

use runner::runner::Runner;

fn main() {
    let args: Vec<String> = env::args().collect();

    match Runner::new(args) {
        Err(error) => {
            eprintln!("{}", error);
            exit(1);
        }
        Ok(runner) => {
            exit(runner.run());
        }
    }
}

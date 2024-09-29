mod common;
mod cross_referencer;
mod parser;
mod runner;
mod tests;
mod tokenizer;
mod transpiler;
mod type_checker;

use std::{path::PathBuf, process::exit};

use clap::{Arg, Command};
use runner::runner::{Runner, RunnerOptions};
use tests::doctests::DocTestRunner;

fn main() {
    let verbose_arg = Arg::new("verbose")
        .short('v')
        .long("verbose")
        .help("Enable verbose output")
        .action(clap::ArgAction::SetTrue);

    let file_arg = Arg::new("file");

    let output_arg = Arg::new("output")
        .short('o')
        .long("output")
        .help("Path of generated binary");

    let doctest_filter = Arg::new("test_or_file")
        .short('t')
        .help("Specify test or file with tests to run");

    let mut command = Command::new("aaa")
        .about("Check, build and run Aaa programs")
        .subcommand(
            Command::new("check")
                .arg(&file_arg)
                .arg(&verbose_arg)
                .about("Check code for syntax- and type errors"),
        )
        .subcommand(
            Command::new("run")
                .arg(&file_arg)
                .arg(&verbose_arg)
                .about("Build executable from code and run it"),
        )
        .subcommand(
            Command::new("build")
                .arg(&file_arg)
                .arg(&verbose_arg)
                .arg(&output_arg)
                .about("Build executable from code without running it"),
        )
        .subcommand(
            Command::new("dev")
                .about("Commands for developing the Aaa language itself")
                .subcommand(
                    Command::new("doctests")
                        .arg(&doctest_filter)
                        .about("Run doctests"),
                ),
        );

    let matches = command.clone().get_matches();

    let mut options = RunnerOptions::default();

    match matches.subcommand() {
        Some(("dev", sub_matches)) => match sub_matches.subcommand() {
            Some(("doctests", doctest_matches)) => {
                let mut test_runner = DocTestRunner::new();

                if let Some(test_or_file) = doctest_matches.get_one::<String>("test_or_file") {
                    test_runner.set_filter(test_or_file);
                }

                exit(test_runner.run());
            }

            _ => {
                command.print_help().unwrap();
                exit(1);
            }
        },
        Some(("run", sub_matches))
        | Some(("check", sub_matches))
        | Some(("build", sub_matches)) => {
            options.command = matches.subcommand().unwrap().0.to_owned();

            if let Some(file) = sub_matches.get_one::<String>("file") {
                options.file = file.clone();
            }
            if sub_matches.get_flag("verbose") {
                options.verbose = true;
            }
        }
        _ => {
            command.print_help().unwrap();
            exit(1);
        }
    }

    if let Some(("build", build_matches)) = matches.subcommand() {
        if let Some(output) = build_matches.get_one::<String>("output") {
            options.output_binary = Some(PathBuf::from(output));
        }
    }

    exit(Runner::run_with_options(options));
}

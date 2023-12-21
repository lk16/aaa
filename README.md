# Aaa
Stack-based language, like forth.

### Contents
The following tools for the Aaa language can be found is this repo
* A [tokenizer](./aaa/tokenizer/) and [parser](./aaa/parser/) for Aaa.
* A [type checker](./aaa/type_checker/)
* A [transpiler to Rust](./aaa/transpiler/)
* A [VS Code extension](./aaa-vscode-extension/README.md) for the Aaa language.
* A lot of tests, written both in python and Aaa

### Examples
```sh
# Run the obligatory hello world example
pdm run ./manage.py run 'fn main { "Hello world\n" . }'

# Run code from a file. Implements the famous fizzbuzz interview question.
pdm run ./manage.py run examples/fizzbuzz.aaa

# Run bare-bones HTTP server in Aaa
pdm run ./manage.py run examples/http/server.aaa

# Send request from different shell
curl http://localhost:8080
```

### Running tests

```sh
# Run tests written in Aaa
pdm run ./manage.py test .

# Run tests written in Python
pdm run pytest
```


### Aaa features
- elementary types (`int`, `bool`, `str`)
- container types (`vec`, `map`)
- type checking
- branching, loops (`if`, `else`, `while`, `foreach`)
- multi-file support (`import`)
- [upcoming](https://github.com/lk16/aaa/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)

### Name
The name of this language is just the first letter of the Latin alphabet repeated three times. When code in this language doesn't work, its meaning becomes an [abbreviation](https://en.uncyclopedia.co/wiki/AAAAAAAAA!).

### Setup
All these commands should be run from the root of this repository.

This project requires python 3.12.1 or newer. Consider using [pyenv](https://github.com/pyenv/pyenv).

```sh
# Download python 3.12.1
pyenv install 3.12.1

# Use it in this project
pyenv local 3.12.1
```

This project also requires rust, see instructions [here](https://www.rust-lang.org/tools/install) on how to install.

After you setup rust and python, run the following commands.

```sh
# Install dependencies
pdm install

# Tell Aaa where the standard library lives
export AAA_STDLIB_PATH=$(pwd)/stdlib

# Run hello world program
pdm run ./manage.py run 'fn main { "Hello world\n" . }'

# Run tests
pdm run pytest
pdm run ./manage.py test .

# Setup pre-commit hooks
pdm run pre-commit install
```

Now you can start running code in Aaa or develop the language!

To enable syntax highlighting for VS Code, enable the [Aaa language extension](./aaa-vscode-extension/README.md)


### Aaa and porth
After watching part of the [Youtube series](https://www.youtube.com/playlist?list=PLpM-Dvs8t0VbMZA7wW9aR3EtBqe2kinu4) on [porth](https://gitlab.com/tsoding/porth), I wanted to make my own stack-based language. Aaa and porth have some similarities, but obviously are not compatible with each other. No code was copied over from the porth repo.

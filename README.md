# Aaa
Stack-based language, like forth.

### Contents
The following tools for the Aaa language can be found is this repo
* A [tokenizer](./aaa/tokenizer/) and [parser](./aaa/parser/) for Aaa. [Grammar](./aaa.lark).
* A [type checker](./aaa/type_checker/)
* A [transpiler to C](./aaa/transpiler/)
* A [VS Code extension](./aaa-vscode-extension/README.md) for the Aaa language.
* A lot of tests, written both in python and Aaa

### Examples
```sh
# Run the obligatory hello world example
./manage.py cmd -cr 'fn main { "Hello world\n" . }'

# Print "aaa\n" using a loop to count to 3
./manage.py cmd -cr 'fn main { "a" 0 while dup 3 < { over . 1 + } drop drop "\n" . }'

# Run code from a file. Implements the famous fizzbuzz interview question.
./manage.py run -cr examples/fizzbuzz.aaa

# Run unit tests
./manage.py runtests

# Run bare-bones HTTP server in Aaa
./manage.py run -cr examples/http_server.aaa

# Send request from different shell
curl http://localhost:8080
```

### Aaa features
- elementary types (`int`, `bool`, `str`)
- container types (`vec`, `map`)
- type checking
- branching, loops (`if`, `else`, `while`, `foreach`)
- multi-file support (`import`)
- [upcoming](https://github.com/lk16/aaa/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)

### Name
The name of this language is just the first letter of the Latin alphabet [repeated](#Examples) three times. When code in this language doesn't work, its meaning becomes an [abbreviation](https://en.uncyclopedia.co/wiki/AAAAAAAAA!).

### Setup
All these commands should be run from the root of this repository.

This project requires python 3.10, consider using [pyenv](https://github.com/pyenv/pyenv).

```sh
# Download python 3.10.2
pyenv install 3.10.2

# Use it in this project
pyenv local 3.10.2
```

After setting up the right python for pdm, run the following commands.

```sh
# Install dependencies
pdm install

# Tell Aaa where the standard library lives
export AAA_STDLIB_PATH=$(pwd)/stdlib

# Run hello world program
pdm run ./manage.py cmd -cr 'fn main { "Hello world\n" . }'

# Run tests
pdm run ./manage.py runtests

# Setup pre-commit hooks
pdm run pre-commit install
```

Now you can start running code in Aaa or develop the language!

To enable syntax highlighting for VS Code, enable the [Aaa language extension](./aaa-vscode-extension/README.md)


### Aaa and porth
After watching part of the [Youtube series](https://www.youtube.com/playlist?list=PLpM-Dvs8t0VbMZA7wW9aR3EtBqe2kinu4) on [porth](https://gitlab.com/tsoding/porth), I wanted to make my own stack-based language. Aaa and porth have some similarities, but obviously are not compatible with each other. No code was copied over from the porth repo.

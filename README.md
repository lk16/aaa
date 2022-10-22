# Aaa
Stack-based language, like forth.

### Contents
* An interpreter for the Aaa language
* A [VS Code extension](./aaa-vscode-extension/README.md) for the Aaa language.
* A lot of tests for the interpreter and the language

### Examples
```sh
# Run the obligatory hello world example
./manage.py cmd 'fn main { "Hello world\n" . }'

# Print "aaa\n" using a loop to count to 3
./manage.py cmd 'fn main { "a" 0 while dup 3 < { over . 1 + } drop drop "\n" . }'

# Run code from a file. Implements the famous fizzbuzz interview question.
./manage.py run examples/fizzbuzz.aaa

# Run unit tests
./manage.py runtests

# Run bare-bones HTTP server in Aaa
./manage.py run examples/http_server.aaa

# Send request from different shell
curl http://localhost:8080
```

### Aaa features
- types and static type checking: (`int`, `bool`, `str`)
- integers and integer instructions (`+`, `-`, `*`, `/`, `%`)
- booleans and boolean instructions (`and`, `or`, `not`)
- strings and string instructions (`+`, `=`)
- stack instructions (`drop`, `dup`, `swap`, `over`, `rot`)
- branching (`if`, `else`)
- loops (`while`)
- functions (`fn`)
- comments (`//`)
- shebang, see below (`#!`)
- multi-file support (`import`)
- [upcoming](./TODO.md)

### Shebang

Starting an aaa source file with `#!/usr/bin/env aaa` allows it to be run just like this `./yourfile.aaa`.
This only works under the following conditions:
* `yourfile.aaa` is executable
* `yourfile.aaa` has a function named `main` that takes no arguments and returns nothing
* `aaa` is in your PATH

Use `chmod +x yourfile.aaa` to make your source file executable. To add `aaa` to path, a [simple script](./run_aaa.sh) is provided we can just symlink from any folder that's in your PATH, for example `ln -s -T $(pwd)/run_aaa.sh ~/.local/bin/aaa`.

If running files using the shebang feels sluggish, it's because `poetry run` is [slow](https://github.com/python-poetry/poetry/issues/3502).

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

# Tell poetry to use it when it creates a virtual environment
poetry env use 3.10
```

After setting up the right python for poetry, run the following commands.

```sh
# Install dependencies
poetry install

# Enter poetry environment
poetry shell

# Tell Aaa where the standard library lives
export AAA_STDLIB_PATH=$(pwd)/stdlib

# Run hello world program
./manage.py cmd 'fn main { "Hello world\n" . }'

# Run tests
./manage.py runtests

# Setup pre-commit hooks
pre-commit install
```

Now you can start running code in Aaa or develop the language!

To enable syntax highlighting for VS Code, enable the [Aaa language extension](./aaa-vscode-extension/README.md)


### Aaa and porth
After watching part of the [Youtube series](https://www.youtube.com/playlist?list=PLpM-Dvs8t0VbMZA7wW9aR3EtBqe2kinu4) on [porth](https://gitlab.com/tsoding/porth), I wanted to make my own stack-based language. Aaa and porth have some similarities, but obviously are not compatible with each other. No code was copied over from the porth repo.

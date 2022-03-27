# Aaa
Stack-based language, like forth.

### Contents
* An interpreter for the Aaa language
* A [VS Code extension](./aaa-vscode-extension/README.md) for the Aaa language.
* A lot of tests for the interpreter and the language

### Examples
```sh
# Run code from a shell argument. This prints "aaa\n".
./aaa.py cmd '"a" 0 while dup 3 < begin over . 1 + end drop drop \n'

# Run code from a file. Implements the famous fizzbuzz interview question.
./aaa.py run examples/fizzbuzz.aaa

# Run unit tests
./aaa.py runtests
```

### Aaa features
- types and static type checking: (`int`, `bool`, `str`)
- integers and integer instructions (`+`, `-`, `*`, `/`, `%`)
- booleans and boolean instructions (`and`, `or`, `not`)
- strings and string instructions (`+`, `=`, `strlen`, `substr`)
- stack instructions (`drop`, `dup`, `swap`, `over`, `rot`)
- branching (`if`, `else`, `end`)
- loops (`while`)
- functions (`fn`)
- comments (`//`)
- shebang, see below (`#!`)
- [upcoming](./TODO.md)

### Shebang

Starting an aaa source file with `#!/usr/bin/env aaa` allows it to be run just like this `./yourfile.aaa`.
This only works under the following conditions:
* `yourfile.aaa` is executable
* `aaa` is in your PATH

Use `chmod +x yourfile.aaa` to make your source file executable. To add `aaa` to path, a [simple script](./run_aaa.sh) is provided we can just symlink from any folder that's in your PATH, for example `ln -s -T $(pwd)/run_aaa.sh ~/.local/bin/aaa`.

If running files using the shebang feels sluggish, it's because `poetry run` is [slow](https://github.com/python-poetry/poetry/issues/3502).

### Name
The name of this language is just the first letter of the Latin alphabet [repeated](#Examples) three times. When code in this language doesn't work, its meaning becomes an [abbreviation](https://en.uncyclopedia.co/wiki/AAAAAAAAA!).

### Setup
All these commands should be run from the root of this repository.

```sh
# Install dependencies
poetry install

# Enter poetry environment
poetry shell
```

To enable syntax highlighting for vs code, enable the [Aaa language extension](./aaa-vscode-extension/README.md)




### Aaa and porth
After watching part of the [Youtube series](https://www.youtube.com/playlist?list=PLpM-Dvs8t0VbMZA7wW9aR3EtBqe2kinu4) on [porth](https://gitlab.com/tsoding/porth), I wanted to make my own stack-based language. Aaa and porth have some similarities, but obviously are not compatible with each other. No code was copied over from the porth repo.

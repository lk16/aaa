# Aaa
Stack-based language, like forth.

### Contents
* An interpreter for the Aaa language
* A [VS Code extension](./aaa-vscode-extension/README.md) for the Aaa language.
* A lot of tests for the interpreter and the language

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


### Examples
```sh
# Run code form a shell argument. This prints "aaa\n".
./aaa.py cmd '"a" 0 true while over . 1 + dup 3 < end drop drop \n'

# Run code from a file. Implements the famous fizzbuzz interview question.
./aaa.py run examples/fizzbuzz.aaa

# Run unit tests
./aaa.py runtests
```

### Aaa features
- types: integers and booleans
- integers and integer operations (`+`, `-`, `*`, `/`, `%`)
- booleans and boolean operations (`and`, `or`, `not`)
- stack operations (`drop`, `dup`, `swap`, `over`, `rot`)
- branching (`if`, `else`, `end`)
- loops (`while`)
- strings and string operations (`+`, `=`, `strlen`, `substr`)
- comments (`//`)

### Upcoming aaa features
- functions (`fn`)
- support shebang (`#!`)
- write a proper grammar
- userfriendly syntax errors
- loops (`break`, `continue`)
- assertions (`assert`)
- debug tools (`breakpoint`)
- support
- static type checking
- structs / classes ?
- compile to native executable
- compile itself

### Aaa and porth
After watching part of the [Youtube series](https://www.youtube.com/playlist?list=PLpM-Dvs8t0VbMZA7wW9aR3EtBqe2kinu4) on [porth](https://gitlab.com/tsoding/porth), I wanted to make my own stack-based language. Aaa and porth have some similarities, but obviously are not compatible with each other. No code was copied over from the porth repo.

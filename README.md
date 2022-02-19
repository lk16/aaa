# Aaa
Stack-based language, like forth.

### Name
The name of this language is just the first letter of the latin alphabet [repeated](https://en.uncyclopedia.co/wiki/AAAAAAAAA!) three times. Unless the code doesn't work as expected, then it's short for Aaaaaaargh.

### How to run
```sh
# Install dependencies and enter poetry environment
poetry install
poetry shell

# Run an Aaa program from shell argument
./aaa.py cmd '1337 . \n'
# prints "1337\n"

./aaa.py cmd '12 2 / 8 * 6 - 42 = if 9001 . end \n'
# prints "9001\n"

# Run an Aaa program from file
./aaa.py run samples/print_number.aaa
# prints "42\n"

# Run unit tests
./aaa.py runtests
```

### Features
- types: integers and booleans
- integers and integer operations
- booleans and boolean operations
- stack operations (`drop`, `dup`, `swap`, `over`, `rot`)
- branching (`if`, `else`, `end`)

### Upcoming features
- branching (`elif`)
- loops (`while`)
- strings
- string operations (`str_print`)
- characters
- character operations (`char_eq`)
- static type checking
- clear syntax errors
- comments (`//`)
- functions (`fn`)
- structs / classes ?
- compile to native executable
- compile itself

### Aaa and porth
Making a forth-like language was strongly inspired by [porth](https://gitlab.com/tsoding/porth), but all code in this repo is written by me.

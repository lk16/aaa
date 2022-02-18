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
./aaa.py cmd '42 print_int'

# Run an Aaa program from file
./aaa.py run samples/print_number.aaa

# Run unit tests
pytest --cov=lang --cov-report=term-missing --pdb -vv
```

### Upcoming features
- math operations (`+`, `-`, `/`, `*`)
- strings
- string operations (`print`)
- booleans
- boolean operations (`not`, `or`, `and`, `=`, `>`, `str_eq`)
- stack operations (`drop`, `dup`)
- branching (`if`, `else`, `end`)
- loops (`while`)
- static type checking
- clear syntax errors
- comments (`//`)
- functions
- structs / classes ?
- compile to native executable
- compile itself

### Aaa and porth
Making a forth-like language was strongly inspired by [porth](https://gitlab.com/tsoding/porth), but all code in this repo is written by me.

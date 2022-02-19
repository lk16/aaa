# Aaa
Stack-based language, like forth.

### Name
The name of this language is just the first letter of the latin alphabet [repeated](#Examples) three times. When code in this language doesn't work its meaning becomes an [abbreviation](https://en.uncyclopedia.co/wiki/AAAAAAAAA!).

### Setup
```sh
# Install dependencies
poetry install

# Enter poetry environment
poetry shell
```

### Examples
```sh
# Run code form a shell argument. This prints "9001\n".
./aaa.py cmd '3 5 + 8 = if 9001 . end \n'

# Show off some features. This prints "aaa\n"
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
- loops (`break`, `continue`)
- assertions (`assert`)
- debug tools (`breakpoint`)
- static type checking
- clear syntax errors
- structs / classes ?
- compile to native executable
- compile itself

### Aaa and porth
Making a forth-like language was strongly inspired by [porth](https://gitlab.com/tsoding/porth), but all code in this repo is written by me.

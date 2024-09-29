# Aaa
Stack-based language, like forth.

TODO improve docs

### Installation
```sh
# Install aaa transpiler and runner tool. Run from repository root.
cargo install --path aaa
```

TODO add tests for examples

### Examples
```sh
# Run the obligatory hello world example
aaa run 'fn main { "Hello world\n" . }'

# Run code from a file. Implements the famous fizzbuzz interview question.
aaa run examples/fizzbuzz.aaa

# Run bare-bones HTTP server in Aaa
aaa run examples/http_server.aaa

# Send request from different shell
curl http://localhost:8080
```

### Running tests

```sh
# Run tests written in Aaa
# TODO this is not implemented yet
aaa test .

# Run tests written in Rust
cargo test --manifest-path aaa/Cargo.toml
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

TODO write this down


### Aaa and porth
After watching part of the [Youtube series](https://www.youtube.com/playlist?list=PLpM-Dvs8t0VbMZA7wW9aR3EtBqe2kinu4) on [porth](https://gitlab.com/tsoding/porth), I wanted to make my own stack-based language. Aaa and porth have some similarities, but obviously are not compatible with each other. No code was copied over from the porth repo.

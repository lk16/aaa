# TODO

### Transpiling to Rust
- [ ] remove `todo!()` occurrences
- [ ] fix `TODO` comments or move them here
- [ ] implement 'paranoid mode' where we check all stack types after every operations

### Const
- [ ] Add tests for const-ness of all builtin functions
- [ ] Add file-scope constants

### This
- [ ] Introduce the special local variable `this` which can only be used in member functions
- [ ] First arg of member functions needs to be called `this` and has no type annotations
- [ ] If `this` is const, the syntax is `const this`

### Improve import system
- Start using colon-separated env var `AAA_PATH` like `PYTHON_PATH`
- Ban absolute imports

### Builtin functions
- Add member functions `map:keys` and `map:values`
- add bitwise or/and/not integer operations
- `/` and `%` should just crash when dividing by zero
- rename `size` functions of `map`, `vec` and `set` to `len`
- move syscalls and env-related functions out of `builtins.aaa`
- `read` and `write` should work with a new buffer type, not a `str`

### Builtin types and typing-features
- `float` type
- union types
- `tuple` type
- interfaces
- better type params for functions
- type params for structs
- `buffer` type (maybe)

### Language features
- debug tools (`breakpoint`)
- global variable (`global`)
- parse itself
- cross reference itself
- type check itself
- transpile itself to Rust

### Language tools
- add command to typecheck files
- add command to reformat files
- more userfriendly syntax errors

### Brag in readme
- minimal dependencies
- tests
- ci
- expressiveness

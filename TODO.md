# TODO

### Enums
- [x] require `enum` to have at least one variant
- [ ] `match` should be have a `case` for all enum variants
- [ ] prevent duplicate cases
- [ ] add `default` case
- [x] make sure all cases handle same enum type
- [ ] make sure there is no `default` when all cases are handled
- [ ] enums with type param variants: `enum foo { x as vec[int] }`
- [ ] recursive enums: `enum foo { x as vec[foo] }`

### Transpiling to C
- [ ] Reset `errno` in case C stdlib functions fail
- [ ] Run `gcov` to find missing coverage
- [ ] Add transpiling to `README.md`
- [ ] Add remaining tests for syscalls `open`, `read`, `write`, `close`, `socket`, `bind`, `listen`, `accept`, `connect` and `fsync`
- [ ] Don't rebuild executables if it's newer than its dependencies

### Improving aaa_stdlib.a
- [ ] container types should contain `aaa_variable` values, not pointers to `aaa_variable`
- [ ] extend `aaa_variable` for different types to reduce `malloc` calls

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

### Verbose mode
- type checker outputs unituitive positiions for FunctionBodyItem's

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
- transpile itself to C

### Language tools
- add command to show instructions per file/function
- add command to typecheck files
- add command to reformat files
- userfriendly syntax errors

### Brag in readme
- minimal dependencies
- tests
- ci
- expressiveness

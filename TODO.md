# TODO

### Transpiling to C
- [x] Implement `repr`
- [x] Update python tests to use `repr` instead of `.`
- [x] Port remaining tests to `test_builtins.aaa`
- [x] Implement missing stdlib functions in C implementation
- [x] Add `-Wconversion`
- [x] Consider other C compiler warning flags
- [ ] Reset `errno` in case C stdlib functions fail
- [ ] Run `gcov` to find missing coverage
- [x] Run `valgrind` to find memory issues
- [x] Add some C source code linter
- [x] Add all of that to CI
- [ ] Add transpiling to `README.md`
- [ ] Add remaining tests for syscalls `open`, `read`, `write`, `close`, `socket`, `bind`, `listen`, `accept`, `connect` and `fsync`
- [x] Build static library of aaa stdlib so we don't compile it everytime
- [ ] Don't rebuild executables if it's newer than its dependencies

### Improving aaa_stdlib.a
- [ ] container types should contain `aaa_variable` values, not pointers to `aaa_variable`
- [ ] extend `aaa_variable` for different types to reduce `malloc` calls

### Const
- [ ] Constant function arguments
    - [x] Test assign to const function arg
    - [x] Test modify field of const function arg
    - [x] Test query field of const function arg and then modifying it
    - [x] add new builtin func `copy`
    - [x] add tests for `copy`
    - [x] rename `vec:get` to `vec:get_copy`
    - [x] make `vec:get` return a duplicate of item in container
    - [x] rename `map:get` to `map:get_copy`
    - [x] make `map:get` return a duplicate of item in container
    - [x] Add tests similar to above
    - [x] Require all iterators to have an `iter` member function returning itself
    - [x] Add `vec_const_iter` and `map_const_iter`
    - [x] Make sure `foreach` calls const versions on `const vec` and `const map`.
    - [x] Add tests for `make_const`
    - [x] Add remaining `const` to `builtins.aaa`
    - [ ] Add tests for const-ness of all builtin functions

- [ ] Constant type params
- [ ] File-scope constants

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
- return early (`return`)
- debug tools (`breakpoint`)
- global variable (`global`)
- support `vec[str]` argument for main function
- support `int` return type for main function
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

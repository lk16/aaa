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
- [ ] Add remaining tests for syscalls
- [ ] Build static library of aaa stdlib so we don't compile it everytime

### Testing
- [ ] Collect coverage stats from dockerized tests
- [ ] Merge coverage of tests in- and outside of docker
- [ ] Cache compiled executables

### Improve import system
- Start using colon-separated env var `AAA_PATH` like `PYTHON_PATH`
- Ban absolute imports

### Builtin functions
- Add member functions `map:keys` and `map:values`
- add binary or/and/not integer operations

### Builtin types and typing-features
- `set` type
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

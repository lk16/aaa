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

### Tests
- add tests for all instructions
- add tests for vscode extension
- add tests that stackbug doesn't happen anymore:
```
fn main {
    while true {
        if false {
            nop
        } else {
            0 drop
        }
    }
}
```

### Containers
- Check that key type is hashable (currently: not a `vec`, `map` or `set`)
- Add member functions:
    - `map:keys`
    - `map:values`
    - `map:items`
- Add `set` container and member functions
- Add a way to iterate over `vec`, `map` and `set`

### Support syscalls
- Add binary or/and/not integer operations
- Consider adding buffer type
- Add network-related functions: socket, bind, listen, accept, ...

### Language features
- `float` type
- rust-like enums
- return early (`return`)
- debug tools (`breakpoint`)
- allow type params for struct
- support `fn main args vec[str] return int { ... }`
- compile to native executable
- compile itself

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

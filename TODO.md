# TODO

### Transpiling to C
- [x] Implement `repr`
- [ ] Update python tests to use `repr` instead of `.`
- [ ] Port remaining tests to `test_builtins.aaa`
- [ ] Move all tests for `.` to one python file
- [ ] Implement missing stdlib functions in `aaa.c`
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

### Instruction optimization
- remove `nop` instructions
- eliminate jumps to jumps
- [constant folding](https://en.wikipedia.org/wiki/Constant_folding)
- removing dead branches

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

# TODO

### Split steps

#### Parse
- [ ] create `Parser` with entrypoint `run()`
- [ ] find dependencies of each file, parse those too
- [ ] detect cyclic imports
- [ ] return dict of filename to parse tree and list of encountered problems

#### Cross Reference
- [ ] create `CrossReferencer` with entrypoint `run()`
- [ ] resolve identifiers of functions/structs/arguments
- [ ] find naming issues
- [ ] return dict of (filename, identifier) to tree with references to other keys in the dict

#### Type Check
- [ ] refactor `TypeChecker` with entrypoint `run()`
- [ ] check if there are no new type placeholders in return type
- [ ] returns list of found problems only

#### Instruction Generation
- [ ] refactor `InstructionGenerator` with entrypoint `run()`
- [ ] accepts return value of `CrossReferencer.run()`
- [ ] replaces function values of the dict by a sequence of instructions
- [ ] returns that

#### Simulation
- [ ] refactor `Simulator` with entrypoint `run()`
- [ ] accepts output of `InstructionGenerator.run()`
- [ ] runs program



### Member functions
- make not returning the object the default

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

## Structs
- This does not crash: `./aaa.py cmd-full 'struct foo { bar as *a } fn main { foo drop }'`

### Containers
- Better error handling for wrong number of type parameters
    - this crashes: `./aaa.py cmd-full 'fn main { nop } fn foo args b as vec { nop }'`
- Member functions should always return the type they operate on as first return value
- Check that key type is hashable (currently: not a `vec`, `map` or `set`)
- Add member functions:
    - `map:keys`
    - `map:values`
    - `map:items`
    - `map:drop`
- Add `set` container and member functions

### Instruction optimization
- remove `nop` instructions
- eliminate jumps to jumps
- [constant folding](https://en.wikipedia.org/wiki/Constant_folding)
- removing dead branches

### Support syscalls
- Add binary or/and/not integer operations
- Consider adding buffer type
- Add basic time-related functions: time, gettimeofday
- Add network-related functions: socket, bind, listen, accept, ...

### Structs
- Allow type params for struct

### Language features
- negative `int` literals
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

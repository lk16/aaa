# TODO

### Tests
- redo all existing exceptions
- fix crash of `./aaa.py cmd-full 'fn main { nop } fn foo args b as vec { nop }'`
- test all instructions
- test vscode extension

### Containers
- Better error handling for wrong number of type parameters
- Member functions should always return the type they operate on as first return value
- Check that key type is hashable (currently: not a `vec`, `map` or `set`)
- Add member functions:
    - `map:keys`
    - `map:values`
    - `map:items`
    - `map:drop`
- Add `set` container and member functions

### Instructions
- create `ContainerOperation` instruction with enum value to select specific one
- create `SysCall` instruction with enum value for various syscalls

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

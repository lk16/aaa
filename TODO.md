# TODO

### Tests
- group existing tests by purpose
- move examples used for testing specific aaa features into python `tests` folder
- redo all existing exceptions
- handle lark parser errors nicely
- string escape sequences
- shallow and deep copying
- keywords can't be used as identifiers
- identifiers can be prefixed with keyword
- member functions can be keyword (such as `map:drop`)

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

### Support syscalls
- Add binary or/and/not integer operations
- Consider adding buffer type
- Add basic file syscalls: open, close, read, write
- Add environment-related functions (not really syscalls)
- Add basic time-related functions: time, gettimeofday
- Add basic process-related functions: getpid, getppid
- Add network-related functions: socket, bind, listen, accept, ...

### Structs
- Allow type params for struct

### Language features
- return early (`return`)
- debug tools (`breakpoint`)
- rust-like enums
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

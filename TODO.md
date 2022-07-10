# TODO

### Syntax and grammar
- replace `begin` and `end` with `{` and `}`

### Tests
- group existing tests by purpose
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

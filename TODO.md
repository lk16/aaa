# TODO

### Aaa file errors
- better tests for exact error messages

### Containers
- Add `vec[TYPE]` and `map[TYPE, TYPE]` to grammar
- Inside function body:
    - `int` should push `0`
    - `bool` should push `false`
    - `str` should push `""`
    - `vec` should push empty vector of correct child element type
    - `map` should push empty map of correct key/value types
- Add syntax for member functions to grammar, for example: `vec.append`
- Member functions should always return the type they operate on as first return value
- Check that key type is hashable (currently: not a `vec` or `map`)
- Add member functions:
    - `vec.get`
    - `vec.set`
    - `vec.append`
    - `vec.size`
    - `vec.empty`
    - `vec.pop`
    - `vec.clear`
    - `vec.copy`
    - `map.get`
    - `map.set`
    - `map.has`
    - `map.size`
    - `map.empty`
    - `map.pop`
    - `map.remove`
    - `map.clear`
    - `map.copy`

### Language features
- structs
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
- custom simple parser, link to grammar.txt
- tests
- ci
- expressiveness

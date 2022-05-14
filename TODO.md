# TODO

### Tests
- test if usage of `builtin_fn` and `builtin_type` outside `AAA_STDLIB_PATH` is banned
- tests for exact error messages

### Containers
- Better error handling for wrong number of type parameters
- Member functions should always return the type they operate on as first return value
- Check that key type is hashable (currently: not a `vec`, `map` or `set`)
- Add member functions:
    - `map:keys`
    - `map:values`
    - `map:items`

### Parser lib
- Add [negative lookbehind](https://stackoverflow.com/a/9306228) so we can add these:
    - use functions (and fields) with `foo.bar` syntax instead of `foo:bar`
    - add `map:drop`
    - add `set` container to builtins

### Structs
- Check associated functions: first arg and return value should be type of struct
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
- custom simple parser, link to grammar.txt
- tests
- ci
- expressiveness

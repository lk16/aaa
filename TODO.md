# TODO

### Singnatures in Aaa code
- introduce env var `AAA_STDLIB_PATH`
- load signatures of `builtin.aaa` before running typechecker
- add `builtin_fn` and `builtin_type` to grammar.txt
- use this instead of signatures `signatures.py`
- ban usage of `builtin_fn` and `builtin_type` outside `AAA_STDLIB_PATH`

### Aaa file errors
- better tests for exact error messages

### Containers
- [ ] Inside function body, type literals should push their zero-value:
    - [x] `int` should push `0`
    - [x] `bool` should push `false`
    - [x] `str` should push `""`
    - [x] `vec` should push empty vector of correct child element type
    - [x] `map` should push empty map of correct key/value types
- [x] Add syntax for member functions to grammar, for example: `vec:append`
- [ ] Better error handling for wrong number of type parameters
- [ ] Member functions should always return the type they operate on as first return value
- [ ] Check that key type is hashable (currently: not a `vec`, `map` or `set`)
- [ ] Make `vec`, `map` and `set` keywords (if not preceded by `:`)
- [ ] Add member functions:
    - [x] `vec:get`
    - [x] `vec:set`
    - [x] `vec:push`
    - [x] `vec:size`
    - [x] `vec:empty`
    - [x] `vec:pop`
    - [x] `vec:clear`
    - [x] `vec:copy`
    - [x] `vec:at`
    - [ ] `map:get`
    - [ ] `map:set`
    - [ ] `map:has_key`
    - [ ] `map:size`
    - [ ] `map:empty`
    - [ ] `map:pop`
    - [ ] `map:remove`
    - [ ] `map:clear`
    - [ ] `map:copy`
    - [ ] `map:keys`
    - [ ] `map:values`

### Parser lib
- Add [negative lookbehind](https://stackoverflow.com/a/9306228) so we can add these:
    - use functions (and fields) with `foo.bar` syntax instead of `foo:bar`
    - add `map:drop`
    - add `set` container to builtins


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

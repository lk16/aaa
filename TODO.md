# TODO

### WIP: static type checking
- move instruction behavior to instruction_types.py
- move instruction signatures to instruction_types.py

- move most debug/verbose stuff from `Simulator` to `Program`
- check that function name and args don't overlap in `Program`
- check that function with same name hasn't been defined already in `Program`
- show errors with line/col number
- save instructions of `Function` inside `Program`
- make `int`, `str` and `bool` reserved tokens in grammar


### Language features
- multi-file programs (`import`)
- return early (`return`)
- assertions (`assert`)
- debug tools (`breakpoint`)
- structs / classes ?
- compile to native executable
- compile itself

### Language tools
- add command to show instructions of all functions with `Program.list_function_instructions()`
- userfriendly syntax errors

### Brag in readme
- minimal dependencies
- custom simple parser, link to grammar.txt
- tests
- ci
- expressiveness

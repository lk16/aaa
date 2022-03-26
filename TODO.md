# TODO

### WIP: static type checking
- rename `Program` to `Simulator`
- create `Program` class that:
    - parses file
    - loads type signatures of all functions
    - type checks all functions
- Use `Program` in `Simulator`
- show errors with line/col number


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

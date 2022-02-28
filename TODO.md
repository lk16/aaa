# TODO

Next development steps.

### Proper Parsing (in [parser](https://github.com/lk16/parser) repo)
- check human error output
- improve test coverage
- check naming consistency
- check for remaining TODO comments
- generate parser from grammar file

### Functions
- implement function arguments
- implement calling functions

### Brag in readme
- minimal dependencies
- custom simple parser, link to grammar.txt
- tests
- ci
- expressiveness

### More umps
- loop jump keywords (`break`, `continue`)

### Be more consistent
- change `while ... end` to `while ... begin ... end`
- change `if ... else ... end` to `if ... begin ... else ... end`

### Function Instructions
- add command to show instructions of all functions with `Program.list_function_instructions()`

### Later
- support comments (`//`)
- support shebang (`#!`)
- userfriendly syntax errors
- multi-file programs (`import`)
- return early (`return`)
- assertions (`assert`)
- debug tools (`breakpoint`)
- static type checking
- structs / classes ?
- compile to native executable
- compile itself

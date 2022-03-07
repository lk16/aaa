# TODO

Next development steps.

### Brag in readme
- minimal dependencies
- custom simple parser, link to grammar.txt
- tests
- ci
- expressiveness

### Forbid empty body of loop/branch/function
- introduce `nop` instruction
- ban empty bodies
- prune

### More jumps
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

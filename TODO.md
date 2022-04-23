# TODO

### Singnatures in Aaa code
- introduce env var `AAA_STDLIB_PATH`
- load signatures of `builtin.aaa` before running typechecker
- add `builtin_fn` and `builtin_type` to grammar.txt
- use this instead of signatures `signatures.py`
- ban usage of `builtin_fn` and `builtin_type` outside `AAA_STDLIB_PATH`

### Improve parser lib

Add this to `Parser._parse()` with `verbose` flag.
```py
expr_token_type = "<None>"
if hasattr(expr, "token_type"):
    expr_token_type = expr.token_type.name

if offset >= len(self.tokens):
    next_token_type = "<EOF>"
else:
    next_token_type = self.tokens[offset].type.name

print(f"_parse() | offset={offset:>3} | expr_token_type={expr_token_type:>30} | next_token_type={next_token_type:>30}")
```


### Aaa file errors
- better tests for exact error messages

### Language features
- return early (`return`)
- debug tools (`breakpoint`)
- structs
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

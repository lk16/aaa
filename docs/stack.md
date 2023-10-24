
### Intro to "the stack"

Aaa is a stack-based language. ALL functions operate on the stack:
* Arguments are consumed ("popped") from the top of the stack
* Returned values are put ("pushed") on top of the stack

Here are some common expressions used when talking about stacks:
* "to push a value": adding a value on top of the stack
* "to pop a value": reading a value from the top of the stack, removing it
* "to drop a value": removing a value from the stack and discarding it

### Syntax basics

This section explains basic syntax to understand the rest of this article. For more details please check the [dedicated article](./syntax.md) on syntax.

Consider this code:
```rs
fn main {
    nop
}
```

It tells us:
* There is a function `main`
* It takes no arguments (there is no `args ...` section)
* It returns nothing (there is no `return ...` section)
* It does nothing (`nop` means do nothing)

Note that we won't use `nop` below. We only use it here because the syntax requires it.

### Pushing values and checking values

Every time we write an integer literal (such as `3`) in the code, it's means: push an integer with this value on the stack. Likewise with booleans (example: `false`), strings (example: `"hello"`). Other types don't have literals.

Here is a program that asserts that 1 + 2 = 3, including some type annotations.

Note that normally we would not write every literal and function call on its own line, but this way we can put comments in between.

```rs
fn main {
    // stack: empty
    1 // stack: 1
    2 // stack: 1 2
    + // stack: 3
    3 // stack: 3 3
    = // stack: true
    assert // stack: empty
}
```

You can see that:
* Every integer literal pushes an integer
* the `+` function takes 2 integer arguments and returns 1 integer
* the `=` function takes 2 integer arguments and returns 1 boolean
* the `assert` function takes 1 boolean and returns nothing

These 3 functions (and all other built-in functions) can be found in the [builtins](../stdlib/builtins.aaa) file.

### Type checking rules

This language comes with a type-checker. Code that breaks the typing rules will not compile (or run for that matter).

The type checker enforces the following rules:
* When calling a function, the correct argument types must be on the top of on the stack
* When defining a function, the correct types must be returned on top of the stack

How this works in detail with `if-else` and other constructs is described in detail in the [typing](./typing.md) article.

### Function argument order

Function arguments get values by consuming items from the stack in the same order they were pushed on the stack. In reality that means we pop the right amount of items from the stack and reverse them. This is a design choice, which helps with readability.

The below code example illustrates this: the function `show_argument_order` has arguments `a` and `b`. It is called after `1` and `2` are pushed on the stack. That means `a` gets assigned a value of `1` and `b` gets assigned a value of `2`.

Note that just before we call `show_argument_order` in `main`, the stack has the value `2` on top of the stack, since it was pushed last.

Also note that the function `show_argument_order` does not return any values, as it has no `return ...` section in its definition. Since function arguments are always consumed from the stack, it means it will just consume two (integer) values from the stack when called.

```rs
fn main {
    // stack: empty
    1  // stack: 1
    2  // stack: 1 2
    show_argument_order // stack: empty
}

fn show_argument_order args a as int, b as int {
    // stack: empty
    a 1 = assert  // asserts `a` has value 1, stack: empty
    b 2 = assert  // asserts `b` has value 2, stack: empty
    // stack: empty
}
```

### Function return value order

Return values are pushed on the stack in the order specified in the `return ...` section of the function declaration.

```rs
fn main {
    // stack: empty
    show_return_value_order // stack: 1 2
    2 = assert // asserts top value is 2, stack: 1
    1 = assert // asserts top value is 1, stack: empty
}

fn show_return_value_order return int, int {
    // stack: empty
    1  // stack: 1
    2  // stack: 1 2
}
```

Dealing with (many) return values can be confusing, so we can use a `use`-block to increase readability.

Note the similarities between a function call and the `use`-block:
* Both consume arguments from the stack
* Both create variables, with values in order these values were pushed on the stack.

```rs
fn main {
    // stack: empty
    show_return_value_order // stack: 1 2
    use a, b {
        a 1 = assert // asserts `a` has value 1, stack: empty
        b 2 = assert // asserts `b` has value 2, stack: empty
    }
}

fn show_return_value_order return int, int {
    // stack: empty
    1  // stack: 1
    2  // stack: 1 2
}
```

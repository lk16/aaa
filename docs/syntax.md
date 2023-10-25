
### Syntax of the Aaa language

TODO

### Syntax of top-level items

TODO

### Syntax describing a function

TODO
* name, args, return, never
* struct associated function
* type parameters

### Syntax inside of functions

TODO
|     Name                        |          Example(s)                                      |
|---------------------------------|----------------------------------------------------------|
| assignment                      | `var <- { ... }`                                         |
| boolean literal                 | either `false` or `true`                                 |
| branch                          | either `if ... { ... }` or `if ... { ... } else { ... }` |
| call from function pointer      | `call`                                                   |
| foreach loop                    | `foreach { ... }`                                        |
| call a function                 | `my_function`                                            |
| function pointer type literal   | `fn[...][...]`                                           |
| get pointer to function         | `my_function fn`                                         |
| integer literal                 | `69` or `-420`                                           |
| match block                     | `match { case ... { ... } default { ... } }`             |
| return                          | `return`                                                 |
| string literal                  | `"hello"` `"\r\n"`                                       |
| get struct field                | `"struct_field_name" ?`                                  |
| set struct field                | `"struct_field_name" { ... }`                            |
| use block                       | `use { ... }`                                            |
| while loop                      | `while { ... }`                                          |

project(Aaa)

cmake_minimum_required(VERSION 3.16)

add_compile_options(
    -std=gnu99
    -g
    -Wall
    -Wextra
    -Werror
    -Wcast-align
    -Wconversion
    -Wfloat-equal
    -Wformat=2
    -Winline
    -Wlogical-op
    -Wmissing-prototypes
    -Wno-missing-braces
    -Wno-missing-field-initializers
    -Wold-style-definition
    -Wpointer-arith
    -Wredundant-decls
    -Wshadow
    -Wstrict-prototypes
    -Wswitch-default
    -Wswitch-enum
    -Wundef
    -Wunreachable-code
)

ADD_LIBRARY(
    aaa_stdlib STATIC
    map.c
    ref_count.c
    stack.c
    str.c
    strbuff.c
    struct.c
    var.c
    vector.c
)

set_target_properties(aaa_stdlib PROPERTIES PREFIX "")

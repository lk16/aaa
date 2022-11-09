#pragma once

#include <stddef.h>
#include <stdbool.h>

#include "str.h"

// TODO make this enum opaque
enum aaa_kind {
    AAA_INTEGER,
    AAA_BOOLEAN,
    AAA_STRING,
    AAA_VECTOR,
    AAA_MAP,
};

// TODO make this struct opaque
struct aaa_variable {
    enum aaa_kind kind;
    union {
        int integer;
        bool boolean;
        struct aaa_string *string;
        struct aaa_vector *vector;
        struct aaa_map *map;
    };
};

struct aaa_string *aaa_variable_repr(const struct aaa_variable *var);
size_t aaa_variable_hash(const struct aaa_variable *var);
bool aaa_variable_equals(const struct aaa_variable *lhs, const struct aaa_variable *rhs);

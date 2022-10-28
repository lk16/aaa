#pragma once

#include <stdbool.h>

enum aaa_kind {
    AAA_INTEGER,
    AAA_BOOLEAN,
    AAA_STRING,
    // TODO add more
};

struct aaa_variable {
    enum aaa_kind kind;
    union {
        int integer;
        bool boolean;
        char *string; // TODO worry about memory leaks
    };
};

struct aaa_stack {
    unsigned size;
    unsigned max_size;
    struct aaa_variable *data;
};

void aaa_stack_init(struct aaa_stack *stack);
void aaa_stack_free(struct aaa_stack *stack);

void aaa_stack_push_int(struct aaa_stack *stack, int value);

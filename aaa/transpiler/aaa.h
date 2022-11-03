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
        const char *string; // TODO worry about memory leaks
    };
};

struct aaa_stack {
    unsigned size;
    unsigned max_size;
    struct aaa_variable *data;
};

void aaa_stack_init(struct aaa_stack *stack);
void aaa_stack_free(struct aaa_stack *stack);

void aaa_stack_not_implemented(struct aaa_stack *stack, const char *aaa_func_name);

void aaa_stack_push_int(struct aaa_stack *stack, int value);
void aaa_stack_push_str(struct aaa_stack *stack, const char *value);
void aaa_stack_push_bool(struct aaa_stack *stack, bool value);
bool aaa_stack_pop_bool(struct aaa_stack *stack);
void aaa_stack_dup(struct aaa_stack *stack);
void aaa_stack_swap(struct aaa_stack *stack);
void aaa_stack_plus(struct aaa_stack *stack);
void aaa_stack_print(struct aaa_stack *stack);
void aaa_stack_less(struct aaa_stack *stack);
void aaa_stack_greater(struct aaa_stack *stack);
void aaa_stack_drop(struct aaa_stack *stack);
void aaa_stack_modulo(struct aaa_stack *stack);
struct aaa_variable *aaa_stack_pop(struct aaa_stack *stack);
void aaa_stack_push_variable(struct aaa_stack *stack, struct aaa_variable *variable);
void aaa_stack_equals(struct aaa_stack *stack);
void aaa_stack_or(struct aaa_stack *stack);
void aaa_stack_socket(struct aaa_stack *stack);
void aaa_stack_not(struct aaa_stack *stack);
void aaa_stack_exit(struct aaa_stack *stack);
void aaa_stack_write(struct aaa_stack *stack);
void aaa_stack_connect(struct aaa_stack *stack);
void aaa_stack_read(struct aaa_stack *stack);
void aaa_stack_bind(struct aaa_stack *stack);
void aaa_stack_listen(struct aaa_stack *stack);
void aaa_stack_accept(struct aaa_stack *stack);

#pragma once

#include <stdbool.h>
#include <stddef.h>

enum aaa_kind {
    AAA_INTEGER,
    AAA_BOOLEAN,
    AAA_STRING,
    AAA_VECTOR,
    // TODO add more
};

struct aaa_variable {
    enum aaa_kind kind;
    union {
        int integer;
        bool boolean;
        const char *string; // TODO worry about memory leaks
        struct aaa_vector *vector;
    };
};

struct aaa_stack {
    size_t size;
    size_t max_size;
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
void aaa_stack_repr(struct aaa_stack *stack);
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
void aaa_stack_assert(struct aaa_stack *stack);
void aaa_stack_over(struct aaa_stack *stack);
void aaa_stack_rot(struct aaa_stack *stack);
void aaa_stack_nop(struct aaa_stack *stack);
void aaa_stack_minus(struct aaa_stack *stack);
void aaa_stack_multiply(struct aaa_stack *stack);
void aaa_stack_divide(struct aaa_stack *stack);
void aaa_stack_less_equal(struct aaa_stack *stack);
void aaa_stack_greater_equal(struct aaa_stack *stack);
void aaa_stack_unequal(struct aaa_stack *stack);
void aaa_stack_and(struct aaa_stack *stack);
void aaa_stack_str_equals(struct aaa_stack *stack);
void aaa_stack_push_vec(struct aaa_stack *stack);

struct aaa_vector {
    size_t size;
    size_t max_size;
    struct aaa_variable *data;
};

void aaa_vector_init(struct aaa_vector *vec);
void aaa_vector_free(struct aaa_vector *vec);

void aaa_vector_clear(struct aaa_vector *vec);
void aaa_vector_copy(struct aaa_vector *vec, struct aaa_vector *copy);
bool aaa_vector_empty(const struct aaa_vector *vec);
struct aaa_variable *aaa_vector_get(struct aaa_vector *vec, size_t offset);
void aaa_vector_pop(struct aaa_vector *vec, struct aaa_variable *popped);
void aaa_vector_push(struct aaa_vector *vec, struct aaa_variable *pushed);
void aaa_vector_set(struct aaa_vector *vec, size_t offset, struct aaa_variable *value);
size_t aaa_vector_size(const struct aaa_vector *vec);


struct aaa_buffer {
    size_t max_size;
    char *data;
    size_t size;
};

void aaa_buffer_init(struct aaa_buffer *buff);
void aaa_buff_append(struct aaa_buffer *buff, const char *str);

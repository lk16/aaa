#pragma once

#include <stdbool.h>
#include <stddef.h>

#include "map.h"
#include "struct.h"
#include "var.h"

struct aaa_stack {
    size_t size;
    size_t max_size;
    struct aaa_variable **data;
};

void aaa_stack_init(struct aaa_stack *stack);
void aaa_stack_free(struct aaa_stack *stack);

void aaa_stack_not_implemented(struct aaa_stack *stack,
                               const char *aaa_func_name);

void aaa_stack_push_int(struct aaa_stack *stack, int value);
void aaa_stack_push_str(struct aaa_stack *stack, struct aaa_string *value);
void aaa_stack_push_str_raw(struct aaa_stack *stack, char *value,
                            bool freeable);
void aaa_stack_push_bool(struct aaa_stack *stack, bool value);
bool aaa_stack_pop_bool(struct aaa_stack *stack);
void aaa_stack_push_struct(struct aaa_stack *stack, struct aaa_struct *s);
struct aaa_struct *aaa_stack_pop_struct(struct aaa_stack *stack);
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
void aaa_stack_push(struct aaa_stack *stack, struct aaa_variable *variable);
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
void aaa_stack_push_vec_empty(struct aaa_stack *stack);
void aaa_stack_push_vec(struct aaa_stack *stack, struct aaa_vector *vector);
void aaa_stack_vec_push(struct aaa_stack *stack);
void aaa_stack_vec_copy(struct aaa_stack *stack);
void aaa_stack_vec_pop(struct aaa_stack *stack);
void aaa_stack_vec_get(struct aaa_stack *stack);
void aaa_stack_vec_set(struct aaa_stack *stack);
void aaa_stack_vec_size(struct aaa_stack *stack);
void aaa_stack_vec_empty(struct aaa_stack *stack);
void aaa_stack_vec_clear(struct aaa_stack *stack);
void aaa_stack_vec_clear(struct aaa_stack *stack);
void aaa_stack_push_map_empty(struct aaa_stack *stack);
void aaa_stack_push_map(struct aaa_stack *stack, struct aaa_map *map);
void aaa_stack_map_set(struct aaa_stack *stack);
void aaa_stack_map_get(struct aaa_stack *stack);
void aaa_stack_map_has_key(struct aaa_stack *stack);
void aaa_stack_map_size(struct aaa_stack *stack);
void aaa_stack_map_empty(struct aaa_stack *stack);
void aaa_stack_map_clear(struct aaa_stack *stack);
void aaa_stack_map_copy(struct aaa_stack *stack);
void aaa_stack_map_pop(struct aaa_stack *stack);
void aaa_stack_map_drop(struct aaa_stack *stack);
void aaa_stack_str_append(struct aaa_stack *stack);
void aaa_stack_str_contains(struct aaa_stack *stack);
void aaa_stack_str_equals(struct aaa_stack *stack);
void aaa_stack_str_join(struct aaa_stack *stack);
void aaa_stack_str_len(struct aaa_stack *stack);
void aaa_stack_str_lower(struct aaa_stack *stack);
void aaa_stack_str_replace(struct aaa_stack *stack);
void aaa_stack_str_split(struct aaa_stack *stack);
void aaa_stack_str_strip(struct aaa_stack *stack);
void aaa_stack_str_upper(struct aaa_stack *stack);
void aaa_stack_str_find_after(struct aaa_stack *stack);
void aaa_stack_str_find(struct aaa_stack *stack);
void aaa_stack_str_substr(struct aaa_stack *stack);
void aaa_stack_str_to_bool(struct aaa_stack *stack);
void aaa_stack_str_to_int(struct aaa_stack *stack);
void aaa_stack_field_query(struct aaa_stack *stack);
void aaa_stack_field_update(struct aaa_stack *stack);
void aaa_stack_fsync(struct aaa_stack *stack);
void aaa_stack_environ(struct aaa_stack *stack);
void aaa_stack_execve(struct aaa_stack *stack);
void aaa_stack_fork(struct aaa_stack *stack);
void aaa_stack_waitpid(struct aaa_stack *stack);

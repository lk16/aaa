#pragma once

#include <stdbool.h>
#include <stddef.h>

#include "types.h"

struct aaa_variable *aaa_variable_new_int(int integer);
struct aaa_variable *aaa_variable_new_bool(bool boolean);
struct aaa_variable *aaa_variable_new_str(struct aaa_string *string);
struct aaa_variable *aaa_variable_new_vector(struct aaa_vector *vector);
struct aaa_variable *aaa_variable_new_map(struct aaa_map *map);
struct aaa_variable *aaa_variable_new_struct(struct aaa_struct *struct_);
struct aaa_variable *aaa_variable_new_vector_iter(struct aaa_vector_iter *iter);

struct aaa_variable *aaa_variable_new_int_zero_value(void);
struct aaa_variable *aaa_variable_new_bool_zero_value(void);
struct aaa_variable *aaa_variable_new_str_zero_value(void);
struct aaa_variable *aaa_variable_new_vector_zero_value(void);
struct aaa_variable *aaa_variable_new_map_zero_value(void);

int aaa_variable_get_int(struct aaa_variable *var);
bool aaa_variable_get_bool(struct aaa_variable *var);
struct aaa_string *aaa_variable_get_str(struct aaa_variable *var);
struct aaa_vector *aaa_variable_get_vector(struct aaa_variable *var);
struct aaa_map *aaa_variable_get_map(struct aaa_variable *var);
struct aaa_struct *aaa_variable_get_struct(struct aaa_variable *var);
struct aaa_vector_iter *aaa_variable_get_vector_iter(struct aaa_variable *var);

struct aaa_string *aaa_variable_repr(const struct aaa_variable *var);
struct aaa_string *aaa_variable_printed(const struct aaa_variable *var);
size_t aaa_variable_hash(const struct aaa_variable *var);
bool aaa_variable_equals(const struct aaa_variable *lhs,
                         const struct aaa_variable *rhs);

void aaa_variable_dec_ref(struct aaa_variable *var);
void aaa_variable_inc_ref(struct aaa_variable *var);

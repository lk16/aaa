#pragma once

#include <stdbool.h>
#include <stddef.h>

#include "types.h"

struct aaa_vector *aaa_vector_new(void);
void aaa_vector_inc_ref(struct aaa_vector *vec);
void aaa_vector_dec_ref(struct aaa_vector *vec);

struct aaa_string *aaa_vector_repr(struct aaa_vector *vec);
bool aaa_vector_equals(struct aaa_vector *lhs, struct aaa_vector *rhs);

void aaa_vector_clear(struct aaa_vector *vec);
struct aaa_vector *aaa_vector_copy(struct aaa_vector *vec);
bool aaa_vector_empty(const struct aaa_vector *vec);
struct aaa_variable *aaa_vector_get(struct aaa_vector *vec, size_t offset);
struct aaa_variable *aaa_vector_pop(struct aaa_vector *vec);
void aaa_vector_push(struct aaa_vector *vec, struct aaa_variable *pushed);
bool aaa_vector_set(struct aaa_vector *vec, size_t offset,
                    struct aaa_variable *value);
size_t aaa_vector_size(const struct aaa_vector *vec);

struct aaa_vector_iter *aaa_vector_iter_new(struct aaa_vector *vec);

void aaa_vector_iter_dec_ref(struct aaa_vector_iter *iter);
void aaa_vector_iter_inc_ref(struct aaa_vector_iter *iter);

bool aaa_vector_iter_next(struct aaa_vector_iter *iter,
                          struct aaa_variable **item);

#pragma once

#include <stdbool.h>
#include <stddef.h>

struct aaa_vector {
    size_t size;
    size_t max_size;
    struct aaa_variable *data;
};

void aaa_vector_init(struct aaa_vector *vec);
void aaa_vector_free(struct aaa_vector *vec);

char *aaa_vec_repr(const struct aaa_vector *vec);

void aaa_vector_clear(struct aaa_vector *vec);
void aaa_vector_copy(struct aaa_vector *vec, struct aaa_vector *copy);
bool aaa_vector_empty(const struct aaa_vector *vec);
void aaa_vector_get(struct aaa_vector *vec, size_t offset, struct aaa_variable *result);
void aaa_vector_pop(struct aaa_vector *vec, struct aaa_variable *popped);
void aaa_vector_push(struct aaa_vector *vec, struct aaa_variable *pushed);
void aaa_vector_set(struct aaa_vector *vec, size_t offset, struct aaa_variable *value);
size_t aaa_vector_size(const struct aaa_vector *vec);

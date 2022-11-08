#include "vector.h"

#include <malloc.h>
#include <stdlib.h>
#include <string.h>

#include "buffer.h"
#include "var.h"

struct aaa_vector {
    size_t size;
    size_t max_size;
    struct aaa_variable *data;
};

struct aaa_vector *aaa_vector_new(void) {
    struct aaa_vector *vec = malloc(sizeof(*vec));
    vec->size = 0;
    vec->max_size = 16;
    vec->data = malloc(vec->max_size * sizeof(*vec->data));
    return vec;
}

void aaa_vector_free(struct aaa_vector *vec) {
    free(vec->data);
    free(vec);
}

char *aaa_vector_repr(const struct aaa_vector *vec) {
    struct aaa_buffer buff;
    aaa_buffer_init(&buff);
    aaa_buffer_append(&buff, "[");

    for (size_t i=0; i<vec->size; i++) {
        struct aaa_variable *item = vec->data + i;

        char *item_repr = aaa_variable_repr(item);
        aaa_buffer_append(&buff, item_repr);

        if (i != vec->size - 1) {
            aaa_buffer_append(&buff, ", ");
        }
    }
    aaa_buffer_append(&buff, "]");

    return buff.data;
}

bool aaa_vector_equals(struct aaa_vector *lhs, struct aaa_vector *rhs) {  // TODO make arguments const
    if (lhs->size != rhs->size) {
        return false;
    }
    for (size_t i=0; i<lhs->size; i++) {
        struct aaa_variable *lhs_item = NULL, *rhs_item = NULL;
        aaa_vector_get(lhs, i, lhs_item);
        aaa_vector_get(rhs, i, rhs_item);
        if (!aaa_variable_equals(lhs_item, rhs_item)) {
            return false;
        }
    }
    return true;
}

void aaa_vector_clear(struct aaa_vector *vec) {
    vec->size = 0;
}

void aaa_vector_copy(struct aaa_vector *vec, struct aaa_vector *copy) {
    (void)vec;
    (void)copy;

    fprintf(stderr, "aaa_vector_copy is not implemented yet!\n");
    abort();
}

bool aaa_vector_empty(const struct aaa_vector *vec) {
    return vec->size == 0;
}

void aaa_vector_get(struct aaa_vector *vec, size_t offset, struct aaa_variable *result) {
    if (offset >= vec->size) {
        fprintf(stderr, "aaa_vector_get out of range\n");
        abort();
    }

    *result = vec->data[offset];
}

void aaa_vector_pop(struct aaa_vector *vec, struct aaa_variable *popped) {
    if (vec->size == 0) {
        fprintf(stderr, "aaa_vector_pop out of range\n");
        abort();
    }

    *popped = vec->data[vec->size - 1];
    vec->size--;
}

static void aaa_vector_resize(struct aaa_vector *vec, size_t new_size) {
    struct aaa_variable *new_data = malloc(new_size * sizeof(*new_data));
    memcpy(new_data, vec->data, vec->max_size * sizeof(*vec->data));
    free(vec->data);
    vec->data = new_data;
    vec->size = new_size;
}

void aaa_vector_push(struct aaa_vector *vec, struct aaa_variable *pushed) {
    if(vec->size == vec->max_size) {
        aaa_vector_resize(vec, 2 * vec->size);
    }

    vec->data[vec->size] = *pushed;
    vec->size++;
}

void aaa_vector_set(struct aaa_vector *vec, size_t offset, struct aaa_variable *value) {
    if (offset >= vec->size) {
        fprintf(stderr, "aaa_vector_set out of range\n");
        abort();
    }

    vec->data[offset] = *value;
}

size_t aaa_vector_size(const struct aaa_vector *vec) {
    return vec->size;
}

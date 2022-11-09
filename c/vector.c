#include <malloc.h>
#include <stdlib.h>
#include <string.h>

#include "vector.h"
#include "buffer.h"
#include "var.h"
#include "ref_count.h"

struct aaa_vector {
    struct aaa_ref_count ref_count;
    size_t size;
    size_t max_size;
    struct aaa_variable **data;
};

struct aaa_vector *aaa_vector_new(void) {
    struct aaa_vector *vec = malloc(sizeof(*vec));
    aaa_ref_count_init(&vec->ref_count);
    vec->size = 0;
    vec->max_size = 16;
    vec->data = malloc(vec->max_size * sizeof(*vec->data));
    for (size_t i=0; i<vec->size; i++) {
        vec->data[i] = NULL;
    }
    return vec;
}

void aaa_vector_dec_ref(struct aaa_vector *vec) {
    if (aaa_ref_count_dec(&vec->ref_count) == 0) {
        for(size_t i=0; i<vec->size; i++) {
            aaa_variable_dec_ref(vec->data[i]);
        }
        free(vec->data);
        free(vec);
    }
}

void aaa_vector_inc_ref(struct aaa_vector *vec) {
    aaa_ref_count_inc(&vec->ref_count);
}

struct aaa_string *aaa_vector_repr(const struct aaa_vector *vec) {
    struct aaa_buffer *buff = aaa_buffer_new();
    aaa_buffer_append(buff, "[");

    for (size_t i=0; i<vec->size; i++) {
        struct aaa_variable *item = vec->data[i];

        struct aaa_string *item_repr = aaa_variable_repr(item);
        aaa_buffer_append(buff, aaa_string_raw(item_repr));
        aaa_string_dec_ref(item_repr);

        if (i != vec->size - 1) {
            aaa_buffer_append(buff, ", ");
        }
    }
    aaa_buffer_append(buff, "]");

    struct aaa_string *string = aaa_buffer_to_string(buff);
    aaa_buffer_dec_ref(buff);
    return string;
}

bool aaa_vector_equals(struct aaa_vector *lhs, struct aaa_vector *rhs) {  // TODO make arguments const
    if (lhs->size != rhs->size) {
        return false;
    }

    for (size_t i=0; i<lhs->size; i++) {
        struct aaa_variable *lhs_item = aaa_vector_get(lhs, i);
        struct aaa_variable *rhs_item = aaa_vector_get(rhs, i);

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

struct aaa_variable *aaa_vector_get(struct aaa_vector *vec, size_t offset) {
    if (offset >= vec->size) {
        fprintf(stderr, "aaa_vector_get out of range\n");
        abort();
    }

    return vec->data[offset];
}

struct aaa_variable *aaa_vector_pop(struct aaa_vector *vec) {
    if (vec->size == 0) {
        fprintf(stderr, "aaa_vector_pop out of range\n");
        abort();
    }

    struct aaa_variable *popped = vec->data[vec->size - 1];
    vec->size--;
    return popped;
}

static void aaa_vector_resize(struct aaa_vector *vec, size_t new_size) {
    struct aaa_variable **new_data = malloc(new_size * sizeof(*new_data));

    for (size_t i=0; i<vec->size; i++) {
        new_data[i] = vec->data[i];
    }

    for (size_t i=vec->size; i<new_size; i++) {
        new_data[i] = NULL;
    }

    free(vec->data);
    vec->data = new_data;
    vec->size = new_size;
}

void aaa_vector_push(struct aaa_vector *vec, struct aaa_variable *pushed) {
    if(vec->size == vec->max_size) {
        aaa_vector_resize(vec, 2 * vec->size);
    }

    vec->data[vec->size] = pushed;
    vec->size++;
}

void aaa_vector_set(struct aaa_vector *vec, size_t offset, struct aaa_variable *value) {
    if (offset >= vec->size) {
        fprintf(stderr, "aaa_vector_set out of range\n");
        abort();
    }

    vec->data[offset] = value;
}

size_t aaa_vector_size(const struct aaa_vector *vec) {
    return vec->size;
}

#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "buffer.h"
#include "map.h"
#include "ref_count.h"
#include "str.h"
#include "struct.h"
#include "var.h"
#include "vector.h"

enum aaa_kind {
    AAA_INTEGER,
    AAA_BOOLEAN,
    AAA_STRING,
    AAA_VECTOR,
    AAA_MAP,
    AAA_STRUCT,
    AAA_VECTOR_ITER,
    AAA_MAP_ITER,
};

struct aaa_variable {
    struct aaa_ref_count ref_count;
    enum aaa_kind kind;
    union {
        int integer;
        bool boolean;
        struct aaa_string *string;
        struct aaa_vector *vector;
        struct aaa_map *map;
        struct aaa_struct *struct_;
        struct aaa_vector_iter *vector_iter;
        struct aaa_map_iter *map_iter;
    };
};

static struct aaa_variable aaa_const_bool_false =
    {{0}, AAA_BOOLEAN, boolean : false};
static struct aaa_variable aaa_const_bool_true =
    {{0}, AAA_BOOLEAN, boolean : true};

static struct aaa_variable aaa_const_ints[11] = {
    {{0}, AAA_INTEGER, integer : 0},  {{0}, AAA_INTEGER, integer : 1},
    {{0}, AAA_INTEGER, integer : 2},  {{0}, AAA_INTEGER, integer : 3},
    {{0}, AAA_INTEGER, integer : 4},  {{0}, AAA_INTEGER, integer : 5},
    {{0}, AAA_INTEGER, integer : 6},  {{0}, AAA_INTEGER, integer : 7},
    {{0}, AAA_INTEGER, integer : 8},  {{0}, AAA_INTEGER, integer : 9},
    {{0}, AAA_INTEGER, integer : 10},
};

static struct aaa_variable *aaa_variable_new(void) {
    struct aaa_variable *var = malloc(sizeof(*var));
    aaa_ref_count_init(&var->ref_count);
    return var;
}

static bool aaa_variable_has_const_int(int integer) {
    int max_const_int = sizeof(aaa_const_ints) / sizeof(aaa_const_ints[0]);
    return integer >= 0 && integer < max_const_int;
}

struct aaa_variable *aaa_variable_new_int(int integer) {
    if (aaa_variable_has_const_int(integer)) {
        return &aaa_const_ints[integer];
    }

    struct aaa_variable *var = aaa_variable_new();
    var->kind = AAA_INTEGER;
    var->integer = integer;
    return var;
}

struct aaa_variable *aaa_variable_new_bool(bool boolean) {
    if (boolean) {
        return &aaa_const_bool_true;
    } else {
        return &aaa_const_bool_false;
    }
}

struct aaa_variable *aaa_variable_new_str(struct aaa_string *string) {
    struct aaa_variable *var = aaa_variable_new();
    var->kind = AAA_STRING;
    var->string = string;
    return var;
}

struct aaa_variable *aaa_variable_new_vector(struct aaa_vector *vector) {
    struct aaa_variable *var = aaa_variable_new();
    var->kind = AAA_VECTOR;
    var->vector = vector;
    return var;
}

struct aaa_variable *aaa_variable_new_map(struct aaa_map *map) {
    struct aaa_variable *var = aaa_variable_new();
    var->kind = AAA_MAP;
    var->map = map;
    return var;
}

struct aaa_variable *aaa_variable_new_struct(struct aaa_struct *struct_) {
    struct aaa_variable *var = aaa_variable_new();
    var->kind = AAA_STRUCT;
    var->struct_ = struct_;
    return var;
}

static struct aaa_string *aaa_variable_repr_bool(bool boolean) {
    char *raw = NULL;
    if (boolean) {
        raw = "true";
    } else {
        raw = "false";
    }
    return aaa_string_new(raw, false);
}

static void aaa_variable_check_kind(const struct aaa_variable *var,
                                    enum aaa_kind kind) {
    if (var->kind != kind) {
        fprintf(stderr, "Aaa type error\n");
        abort();
    }
}

int aaa_variable_get_int(struct aaa_variable *var) {
    aaa_variable_check_kind(var, AAA_INTEGER);
    return var->integer;
}

bool aaa_variable_get_bool(struct aaa_variable *var) {
    aaa_variable_check_kind(var, AAA_BOOLEAN);
    return var->boolean;
}

struct aaa_string *aaa_variable_get_str(struct aaa_variable *var) {
    aaa_variable_check_kind(var, AAA_STRING);
    return var->string;
}

struct aaa_vector *aaa_variable_get_vector(struct aaa_variable *var) {
    aaa_variable_check_kind(var, AAA_VECTOR);
    return var->vector;
}

struct aaa_map *aaa_variable_get_map(struct aaa_variable *var) {
    aaa_variable_check_kind(var, AAA_MAP);
    return var->map;
}

struct aaa_struct *aaa_variable_get_struct(struct aaa_variable *var) {
    aaa_variable_check_kind(var, AAA_STRUCT);
    return var->struct_;
}

static struct aaa_string *aaa_variable_repr_int(int integer) {
    size_t buff_size = (size_t)snprintf(NULL, 0, "%d", integer);
    char *buff = malloc(buff_size + 1);
    snprintf(buff, buff_size + 1, "%d", integer);
    return aaa_string_new(buff, true);
}

static struct aaa_string *aaa_variable_repr_str(struct aaa_string *string) {
    struct aaa_buffer *buff = aaa_buffer_new();
    aaa_buffer_append(buff, "\"");
    const char *c = aaa_string_raw(string);

    while (*c) {
        switch (*c) {
            case '\a':
                aaa_buffer_append(buff, "\\a");
                break;
            case '\b':
                aaa_buffer_append(buff, "\\b");
                break;
            case '\f':
                aaa_buffer_append(buff, "\\f");
                break;
            case '\n':
                aaa_buffer_append(buff, "\\n");
                break;
            case '\r':
                aaa_buffer_append(buff, "\\r");
                break;
            case '\t':
                aaa_buffer_append(buff, "\\t");
                break;
            case '\v':
                aaa_buffer_append(buff, "\\v");
                break;
            case '\\':
                aaa_buffer_append(buff, "\\\\");
                break;
            case '\'':
                aaa_buffer_append(buff, "\\'");
                break;
            case '\"':
                aaa_buffer_append(buff, "\\\"");
                break;
            default:
                (void)0;
                char str[2] = "\0";
                str[0] = *c;
                aaa_buffer_append(buff, str);
        }
        c++;
    }
    aaa_buffer_append(buff, "\"");
    struct aaa_string *repr = aaa_buffer_to_string(buff);
    aaa_buffer_dec_ref(buff);
    return repr;
}

struct aaa_string *aaa_variable_repr(const struct aaa_variable *var) {
    switch (var->kind) {
        case AAA_BOOLEAN:
            return aaa_variable_repr_bool(var->boolean);
        case AAA_INTEGER:
            return aaa_variable_repr_int(var->integer);
        case AAA_STRING:
            return aaa_variable_repr_str(var->string);
        case AAA_VECTOR:
            return aaa_vector_repr(var->vector);
        case AAA_MAP:
            return aaa_map_repr(var->map);
        case AAA_STRUCT:
        case AAA_VECTOR_ITER:
        case AAA_MAP_ITER:
        default:
            fprintf(stderr, "aaa_variable_repr Unhandled variable kind\n");
            abort();
    }
}

struct aaa_string *aaa_variable_printed(const struct aaa_variable *var) {
    if (var->kind == AAA_STRING) {
        aaa_string_inc_ref(var->string);
        return var->string;
    }

    return aaa_variable_repr(var);
}

size_t aaa_variable_hash(const struct aaa_variable *var) {
    switch (var->kind) {
        case AAA_BOOLEAN:
            if (var->boolean) {
                return 1;
            } else {
                return 0;
            }
        case AAA_INTEGER:
            return (size_t)(var->integer ^ 0x123456789) +
                   (size_t)(var->integer << 13) + (size_t)(var->integer >> 17);
        case AAA_STRING:
            (void)0;
            size_t hash = 0;
            const char *c = aaa_string_raw(var->string);
            while (*c) {
                hash = (hash * 123457) + (size_t)(*c);
                c++;
            }
            return hash;
        case AAA_VECTOR:
            fprintf(stderr, "Cannot hash a vector!\n");
            abort();
        case AAA_MAP:
            fprintf(stderr, "Cannot hash a map!\n");
            abort();
        case AAA_STRUCT:
        case AAA_VECTOR_ITER:
        case AAA_MAP_ITER:
        default:
            fprintf(stderr, "aaa_variable_hash Unhandled variable kind\n");
            abort();
    }
}

bool aaa_variable_equals(const struct aaa_variable *lhs,
                         const struct aaa_variable *rhs) {
    if (lhs->kind != rhs->kind) {
        return false;
    }

    switch (lhs->kind) {
        case AAA_BOOLEAN:
            return lhs->boolean == rhs->boolean;
        case AAA_INTEGER:
            return lhs->integer == rhs->integer;
        case AAA_STRING:
            return aaa_string_equals(lhs->string, rhs->string);
        case AAA_VECTOR:
            return aaa_vector_equals(lhs->vector, rhs->vector);
        case AAA_MAP:
        case AAA_STRUCT:
        case AAA_VECTOR_ITER:
        case AAA_MAP_ITER:
        default:
            fprintf(stderr, "aaa_variable_equals Unhandled variable kind\n");
            abort();
    }
}

void aaa_variable_dec_ref(struct aaa_variable *var) {
    if (!var) {
        return;
    }

    switch (var->kind) {
        case AAA_BOOLEAN:
            return;
        case AAA_INTEGER:
            if (aaa_variable_has_const_int(var->integer)) {
                return;
            }
            break;
        case AAA_STRING:
            aaa_string_dec_ref(var->string);
            break;
        case AAA_VECTOR:
            aaa_vector_dec_ref(var->vector);
            break;
        case AAA_MAP:
            aaa_map_dec_ref(var->map);
            break;
        case AAA_STRUCT:
            aaa_struct_dec_ref(var->struct_);
            break;
        case AAA_VECTOR_ITER:
            aaa_vector_iter_dec_ref(var->vector_iter);
            break;
        case AAA_MAP_ITER:
            aaa_map_iter_dec_ref(var->map_iter);
            break;
        default:
            fprintf(stderr, "aaa_variable_dec_ref unhandled variable kind\n");
            abort();
    }
    if (aaa_ref_count_dec(&var->ref_count) == 0) {
        free(var);
    }
}

void aaa_variable_inc_ref(struct aaa_variable *var) {
    switch (var->kind) {
        case AAA_BOOLEAN:
            return;
        case AAA_INTEGER:
            break;
        case AAA_STRING:
            aaa_string_inc_ref(var->string);
            break;
        case AAA_VECTOR:
            aaa_vector_inc_ref(var->vector);
            break;
        case AAA_MAP:
            aaa_map_inc_ref(var->map);
            break;
        case AAA_STRUCT:
            aaa_struct_inc_ref(var->struct_);
            break;
        case AAA_VECTOR_ITER:
            aaa_vector_iter_inc_ref(var->vector_iter);
            break;
        case AAA_MAP_ITER:
            aaa_map_iter_inc_ref(var->map_iter);
            break;
        default:
            fprintf(stderr, "aaa_variable_inc_ref unhandled variable kind\n");
            abort();
    }
    aaa_ref_count_inc(&var->ref_count);
}

struct aaa_variable *aaa_variable_new_int_zero_value(void) {
    return aaa_variable_new_int(0);
}

struct aaa_variable *aaa_variable_new_bool_zero_value(void) {
    return aaa_variable_new_bool(false);
}

struct aaa_variable *aaa_variable_new_str_zero_value(void) {
    struct aaa_string *string = aaa_string_new("", false);
    return aaa_variable_new_str(string);
}

struct aaa_variable *aaa_variable_new_vector_zero_value(void) {
    struct aaa_vector *vector = aaa_vector_new();
    return aaa_variable_new_vector(vector);
}

struct aaa_variable *aaa_variable_new_map_zero_value(void) {
    struct aaa_map *map = aaa_map_new();
    return aaa_variable_new_map(map);
}

struct aaa_variable *
aaa_variable_new_vector_iter(struct aaa_vector_iter *iter) {
    struct aaa_variable *var = aaa_variable_new();
    var->vector_iter = iter;
    var->kind = AAA_VECTOR_ITER;
    return var;
}

struct aaa_vector_iter *aaa_variable_get_vector_iter(struct aaa_variable *var) {
    return var->vector_iter;
}

struct aaa_variable *aaa_variable_new_map_iter(struct aaa_map_iter *iter) {
    struct aaa_variable *var = aaa_variable_new();
    var->map_iter = iter;
    var->kind = AAA_MAP_ITER;
    return var;
}

struct aaa_map_iter *aaa_variable_get_map_iter(struct aaa_variable *var) {
    return var->map_iter;
}

#include <stdio.h>
#include <malloc.h>
#include <stdlib.h>
#include <string.h>

#include "str.h"
#include "buffer.h"
#include "vector.h"
#include "map.h"
#include "var.h"

enum aaa_kind {
    AAA_INTEGER,
    AAA_BOOLEAN,
    AAA_STRING,
    AAA_VECTOR,
    AAA_MAP,
};

struct aaa_variable {
    enum aaa_kind kind;
    union {
        int integer;
        bool boolean;
        struct aaa_string *string;
        struct aaa_vector *vector;
        struct aaa_map *map;
    };
};

static struct aaa_variable *aaa_variable_new(void) {
    struct aaa_variable *var = malloc(sizeof(*var));
    return var;
}

struct aaa_variable *aaa_variable_new_int(int integer) {
    struct aaa_variable *var = aaa_variable_new();
    var->kind = AAA_INTEGER;
    var->integer = integer;
    return var;
}

struct aaa_variable *aaa_variable_new_bool(bool boolean) {
    struct aaa_variable *var = aaa_variable_new();
    var->kind = AAA_BOOLEAN;
    var->boolean = boolean;
    return var;
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

struct aaa_string *aaa_variable_repr_bool(bool boolean) {
    char *raw = NULL;
    if (boolean) {
        raw = "true";
    } else {
        raw = "false";
    }
    return aaa_string_new(raw, false);
}

static void aaa_variable_check_kind(const struct aaa_variable *var, enum aaa_kind kind) {
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

struct aaa_string *aaa_variable_repr_int(int integer) {
    size_t buff_size = snprintf(NULL, 0, "%d", integer);
    char *buff = malloc(buff_size + 1);
    snprintf(buff, buff_size + 1, "%d", integer);
    return aaa_string_new(buff, true);
}

struct aaa_string *aaa_variable_repr_str(struct aaa_string *string) {
    struct aaa_buffer *buff = aaa_buffer_new();
    aaa_buffer_append(buff, "\"");
    const char *c = aaa_string_raw(string);

    while (*c) {
        switch (*c) {
            case '\a': aaa_buffer_append(buff, "\\a"); break;
            case '\b': aaa_buffer_append(buff, "\\b"); break;
            case '\f': aaa_buffer_append(buff, "\\f"); break;
            case '\n': aaa_buffer_append(buff, "\\n"); break;
            case '\r': aaa_buffer_append(buff, "\\r"); break;
            case '\t': aaa_buffer_append(buff, "\\t"); break;
            case '\v': aaa_buffer_append(buff, "\\v"); break;
            case '\\': aaa_buffer_append(buff, "\\\\"); break;
            case '\'': aaa_buffer_append(buff, "\\'"); break;
            case '\"': aaa_buffer_append(buff, "\\\""); break;
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
        case AAA_BOOLEAN: return aaa_variable_repr_bool(var->boolean);
        case AAA_INTEGER: return aaa_variable_repr_int(var->integer);
        case AAA_STRING:  return aaa_variable_repr_str(var->string);
        case AAA_VECTOR:  return aaa_vector_repr(var->vector);
        case AAA_MAP:     return aaa_map_repr(var->map);
        default:
            fprintf(stderr, "aaa_variable_repr Unhandled variable kind\n");
            abort();
    }
}

struct aaa_string *aaa_variable_printed(const struct aaa_variable *var) {
    if (var->kind == AAA_STRING) {
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
            return (var->integer ^ 0x123456789) + (var->integer << 13) + (var->integer >> 17);
        case AAA_STRING:
            (void)0;
            size_t hash = 0;
            const char *c = aaa_string_raw(var->string);
            while (*c) {
                hash = (hash * 123457) + *c;
                c++;
            }
            return hash;
        case AAA_VECTOR:
            fprintf(stderr, "Cannot hash a vector!\n");
            abort();
        default:
            fprintf(stderr, "aaa_variable_hash Unhandled variable kind\n");
            abort();
    }
}

bool aaa_variable_equals(const struct aaa_variable *lhs, const struct aaa_variable *rhs) {
    if (lhs->kind != rhs->kind) {
        return false;
    }

    switch (lhs->kind) {
        case AAA_BOOLEAN:
            return lhs->boolean == rhs->boolean;
        case AAA_INTEGER:
            return lhs->integer == rhs->integer;
        case AAA_STRING:
            (void)0;
            const char *lhs_raw = aaa_string_raw(lhs->string);
            const char *rhs_raw = aaa_string_raw(rhs->string);
            return strcmp(lhs_raw, rhs_raw) == 0;
        case AAA_VECTOR:
            return aaa_vector_equals(lhs->vector, rhs->vector);
        default:
            fprintf(stderr, "aaa_variable_equals Unhandled variable kind\n");
            abort();
    }
}

void aaa_variable_dec_ref(struct aaa_variable *var) {
    switch (var->kind) {
        case AAA_BOOLEAN: break;
        case AAA_INTEGER: break;
        case AAA_STRING: aaa_string_dec_ref(var->string); break;
        case AAA_VECTOR: aaa_vector_dec_ref(var->vector); break;
        case AAA_MAP: break; // TODO
        default:
            fprintf(stderr, "aaa_variable_dec_ref unhandled variable kind\n");
            abort();
    }
}

void aaa_variable_inc_ref(struct aaa_variable *var) {
    switch(var->kind) {
        case AAA_BOOLEAN: break;
        case AAA_INTEGER: break;
        case AAA_STRING: aaa_string_inc_ref(var->string); break;
        case AAA_VECTOR: aaa_vector_inc_ref(var->vector); break;
        case AAA_MAP: break;  // TODO
        default:
            fprintf(stderr, "aaa_variable_inc_ref unhandled variable kind\n");
            abort();
    }
}
